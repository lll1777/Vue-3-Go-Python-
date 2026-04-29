from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import logging
import uuid
import threading
import time
import requests
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
CORS(app, supports_credentials=True)

UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CALLBACK_TIMEOUT = 30
MAX_RETRY_COUNT = 3

from rule_engine import RuleEngine
from image_analysis import ImageAnalyzer
from case_matcher import CaseMatcher
from seller_score import SellerScoreCalculator
from nlp_analyzer import NLPAnalyzer

rule_engine = RuleEngine()
image_analyzer = ImageAnalyzer()
case_matcher = CaseMatcher()
seller_score_calc = SellerScoreCalculator()
nlp_analyzer = NLPAnalyzer()


@dataclass
class AnalysisRequest:
    request_id: str
    ticket_id: int
    evidence_id: int
    analysis_type: str
    callback_url: Optional[str] = None
    status: str = 'pending'
    created_at: datetime = field(default_factory=datetime.now)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0


class AsyncAnalysisManager:
    def __init__(self):
        self.requests: Dict[str, AnalysisRequest] = {}
        self._lock = threading.Lock()

    def create_request(
        self,
        ticket_id: int,
        evidence_id: int,
        analysis_type: str,
        callback_url: Optional[str] = None
    ) -> AnalysisRequest:
        request_id = str(uuid.uuid4())
        with self._lock:
            req = AnalysisRequest(
                request_id=request_id,
                ticket_id=ticket_id,
                evidence_id=evidence_id,
                analysis_type=analysis_type,
                callback_url=callback_url,
                status='pending'
            )
            self.requests[request_id] = req
        return req

    def get_request(self, request_id: str) -> Optional[AnalysisRequest]:
        with self._lock:
            return self.requests.get(request_id)

    def update_request(
        self,
        request_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> bool:
        with self._lock:
            req = self.requests.get(request_id)
            if req:
                req.status = status
                req.result = result
                req.error = error
                return True
        return False

    def validate_request(
        self,
        request_id: str,
        ticket_id: int,
        evidence_id: int
    ) -> tuple[bool, str]:
        req = self.get_request(request_id)
        if not req:
            return False, f"Analysis request not found: {request_id}"

        if req.ticket_id != ticket_id:
            return False, f"Ticket ID mismatch: expected {req.ticket_id}, got {ticket_id}"

        if req.evidence_id != evidence_id:
            return False, f"Evidence ID mismatch: expected {req.evidence_id}, got {evidence_id}"

        if req.status == 'completed' or req.status == 'failed':
            return False, f"Request already processed: {req.status}"

        return True, "Validation successful"


async_analysis_manager = AsyncAnalysisManager()


def send_callback(
    callback_url: str,
    request_id: str,
    ticket_id: int,
    evidence_id: int,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    retry_count: int = 0
) -> bool:
    if not callback_url:
        logger.warning("No callback URL provided")
        return True

    payload = {
        'request_id': request_id,
        'ticket_id': ticket_id,
        'evidence_id': evidence_id,
        'status': status,
        'completed_at': datetime.now().isoformat()
    }

    if result:
        payload['result'] = result
    if error:
        payload['error'] = error

    try:
        logger.info(f"Sending callback to {callback_url} for request {request_id}")
        response = requests.post(
            callback_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=CALLBACK_TIMEOUT
        )

        if response.status_code in [200, 201, 202]:
            logger.info(f"Callback successful for request {request_id}")
            return True
        else:
            logger.warning(f"Callback returned status {response.status_code}: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"Callback failed for request {request_id}: {str(e)}")
        return False


def process_async_analysis(
    request: AnalysisRequest,
    file_path: str,
    cleanup_file: bool = True
):
    try:
        logger.info(f"Starting async analysis for request {request.request_id}")

        async_analysis_manager.update_request(
            request.request_id,
            status='processing'
        )

        result = image_analyzer.analyze(file_path, request.analysis_type)

        async_analysis_manager.update_request(
            request.request_id,
            status='completed',
            result=result
        )

        logger.info(f"Analysis completed for request {request.request_id}")

        if request.callback_url:
            success = send_callback(
                callback_url=request.callback_url,
                request_id=request.request_id,
                ticket_id=request.ticket_id,
                evidence_id=request.evidence_id,
                status='completed',
                result=result
            )

            if not success:
                logger.warning(f"Callback failed for request {request.request_id}, but analysis completed")

    except Exception as e:
        logger.error(f"Async analysis failed for request {request.request_id}: {str(e)}")
        async_analysis_manager.update_request(
            request.request_id,
            status='failed',
            error=str(e)
        )

        if request.callback_url:
            send_callback(
                callback_url=request.callback_url,
                request_id=request.request_id,
                ticket_id=request.ticket_id,
                evidence_id=request.evidence_id,
                status='failed',
                error=str(e)
            )

    finally:
        if cleanup_file and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up file {file_path}: {str(e)}")


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'ML Service',
        'version': '1.0.0'
    })


@app.route('/api/rule-engine/evaluate', methods=['POST'])
def evaluate_rules():
    try:
        data = request.get_json()
        ticket_data = data.get('ticket', {})
        evidences = data.get('evidences', [])
        rules = data.get('rules', None)

        result = rule_engine.evaluate(ticket_data, evidences, rules)
        return jsonify({
            'code': 200,
            'data': result
        })
    except Exception as e:
        logger.error(f"Rule evaluation error: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500


@app.route('/api/rule-engine/test', methods=['POST'])
def test_rule():
    try:
        data = request.get_json()
        rule = data.get('rule', {})
        test_data = data.get('test_data', {})

        result = rule_engine.test_rule(rule, test_data)
        return jsonify({
            'code': 200,
            'data': result
        })
    except Exception as e:
        logger.error(f"Rule test error: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500


@app.route('/api/image/analyze', methods=['POST'])
def analyze_image():
    try:
        if 'file' not in request.files:
            return jsonify({
                'code': 400,
                'message': 'No file uploaded'
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'code': 400,
                'message': 'No selected file'
            }), 400

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        analysis_type = request.form.get('analysis_type', 'all')
        result = image_analyzer.analyze(file_path, analysis_type)

        os.remove(file_path)

        return jsonify({
            'code': 200,
            'data': result
        })
    except Exception as e:
        logger.error(f"Image analysis error: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500


@app.route('/api/image/false-advertising', methods=['POST'])
def detect_false_advertising():
    try:
        if 'file' not in request.files:
            return jsonify({
                'code': 400,
                'message': 'No file uploaded'
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'code': 400,
                'message': 'No selected file'
            }), 400

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        context = request.form.get('context', None)
        result = image_analyzer.detect_false_advertising(file_path, context)

        os.remove(file_path)

        return jsonify({
            'code': 200,
            'data': result
        })
    except Exception as e:
        logger.error(f"False advertising detection error: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500


@app.route('/api/image/quality-issues', methods=['POST'])
def detect_quality_issues():
    try:
        if 'file' not in request.files:
            return jsonify({
                'code': 400,
                'message': 'No file uploaded'
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'code': 400,
                'message': 'No selected file'
            }), 400

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        result = image_analyzer.detect_quality_issues(file_path)

        os.remove(file_path)

        return jsonify({
            'code': 200,
            'data': result
        })
    except Exception as e:
        logger.error(f"Quality issues detection error: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500


@app.route('/api/cases/match', methods=['POST'])
def match_cases():
    try:
        data = request.get_json()
        ticket_data = data.get('ticket', {})
        limit = data.get('limit', 5)

        result = case_matcher.match_similar_cases(ticket_data, limit)
        return jsonify({
            'code': 200,
            'data': result
        })
    except Exception as e:
        logger.error(f"Case matching error: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500


@app.route('/api/cases/search', methods=['GET'])
def search_cases():
    try:
        query = request.args.get('query', '')
        category = request.args.get('category', '')
        limit = int(request.args.get('limit', 10))

        result = case_matcher.search_cases(query, category, limit)
        return jsonify({
            'code': 200,
            'data': result
        })
    except Exception as e:
        logger.error(f"Case search error: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500


@app.route('/api/cases/analyze-decision', methods=['POST'])
def analyze_case_decision():
    try:
        data = request.get_json()
        case_data = data.get('case', {})
        ticket_data = data.get('ticket', {})

        result = case_matcher.analyze_decision(case_data, ticket_data)
        return jsonify({
            'code': 200,
            'data': result
        })
    except Exception as e:
        logger.error(f"Case decision analysis error: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500


@app.route('/api/seller-score/calculate', methods=['POST'])
def calculate_seller_score():
    try:
        data = request.get_json()
        seller_data = data.get('seller', {})
        history = data.get('history', [])

        result = seller_score_calc.calculate_score(seller_data, history)
        return jsonify({
            'code': 200,
            'data': result
        })
    except Exception as e:
        logger.error(f"Seller score calculation error: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500


@app.route('/api/seller-score/update', methods=['POST'])
def update_seller_score():
    try:
        data = request.get_json()
        current_score = data.get('current_score', 100.0)
        decision = data.get('decision', '')
        amount = data.get('amount', 0.0)
        seller_stats = data.get('seller_stats', {})

        result = seller_score_calc.update_score(
            current_score,
            decision,
            amount,
            seller_stats
        )
        return jsonify({
            'code': 200,
            'data': result
        })
    except Exception as e:
        logger.error(f"Seller score update error: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500


@app.route('/api/seller-score/predict', methods=['POST'])
def predict_seller_score():
    try:
        data = request.get_json()
        seller_data = data.get('seller', {})
        ticket_data = data.get('ticket', {})

        result = seller_score_calc.predict_impact(seller_data, ticket_data)
        return jsonify({
            'code': 200,
            'data': result
        })
    except Exception as e:
        logger.error(f"Seller score prediction error: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500


@app.route('/api/nlp/analyze', methods=['POST'])
def analyze_text():
    try:
        data = request.get_json()
        text = data.get('text', '')
        analysis_type = data.get('analysis_type', 'all')

        result = nlp_analyzer.analyze(text, analysis_type)
        return jsonify({
            'code': 200,
            'data': result
        })
    except Exception as e:
        logger.error(f"NLP analysis error: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500


@app.route('/api/nlp/classify-complaint', methods=['POST'])
def classify_complaint():
    try:
        data = request.get_json()
        text = data.get('text', '')
        title = data.get('title', '')

        result = nlp_analyzer.classify_complaint(text, title)
        return jsonify({
            'code': 200,
            'data': result
        })
    except Exception as e:
        logger.error(f"Complaint classification error: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500


@app.route('/api/nlp/extract-keywords', methods=['POST'])
def extract_keywords():
    try:
        data = request.get_json()
        text = data.get('text', '')
        top_k = data.get('top_k', 10)

        result = nlp_analyzer.extract_keywords(text, top_k)
        return jsonify({
            'code': 200,
            'data': result
        })
    except Exception as e:
        logger.error(f"Keyword extraction error: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500


@app.route('/api/image/async-analyze', methods=['POST'])
def async_analyze_image():
    try:
        if 'file' not in request.files:
            return jsonify({
                'code': 400,
                'message': 'No file uploaded'
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'code': 400,
                'message': 'No selected file'
            }), 400

        ticket_id = request.form.get('ticket_id')
        evidence_id = request.form.get('evidence_id')
        callback_url = request.form.get('callback_url')
        analysis_type = request.form.get('analysis_type', 'all')

        if not ticket_id or not evidence_id:
            return jsonify({
                'code': 400,
                'message': 'ticket_id and evidence_id are required'
            }), 400

        try:
            ticket_id_int = int(ticket_id)
            evidence_id_int = int(evidence_id)
        except ValueError:
            return jsonify({
                'code': 400,
                'message': 'Invalid ticket_id or evidence_id'
            }), 400

        file_path = os.path.join(
            app.config['UPLOAD_FOLDER'],
            f"{ticket_id}_{evidence_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
        )
        file.save(file_path)

        analysis_request = async_analysis_manager.create_request(
            ticket_id=ticket_id_int,
            evidence_id=evidence_id_int,
            analysis_type=analysis_type,
            callback_url=callback_url
        )

        thread = threading.Thread(
            target=process_async_analysis,
            args=(analysis_request, file_path, True)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'code': 202,
            'message': 'Analysis request accepted',
            'data': {
                'request_id': analysis_request.request_id,
                'ticket_id': analysis_request.ticket_id,
                'evidence_id': analysis_request.evidence_id,
                'status': analysis_request.status,
                'callback_url': analysis_request.callback_url
            }
        })

    except Exception as e:
        logger.error(f"Async analysis error: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500


@app.route('/api/image/analyze/<request_id>', methods=['GET'])
def get_analysis_status(request_id):
    try:
        req = async_analysis_manager.get_request(request_id)
        if not req:
            return jsonify({
                'code': 404,
                'message': f"Analysis request not found: {request_id}"
            }), 404

        return jsonify({
            'code': 200,
            'data': {
                'request_id': req.request_id,
                'ticket_id': req.ticket_id,
                'evidence_id': req.evidence_id,
                'status': req.status,
                'result': req.result,
                'error': req.error,
                'created_at': req.created_at.isoformat()
            }
        })

    except Exception as e:
        logger.error(f"Get analysis status error: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500


@app.route('/api/image/validate', methods=['POST'])
def validate_analysis_request():
    try:
        data = request.get_json()
        request_id = data.get('request_id')
        ticket_id = data.get('ticket_id')
        evidence_id = data.get('evidence_id')

        if not all([request_id, ticket_id, evidence_id]):
            return jsonify({
                'code': 400,
                'message': 'request_id, ticket_id, and evidence_id are required'
            }), 400

        try:
            ticket_id_int = int(ticket_id)
            evidence_id_int = int(evidence_id)
        except ValueError:
            return jsonify({
                'code': 400,
                'message': 'Invalid ticket_id or evidence_id'
            }), 400

        is_valid, message = async_analysis_manager.validate_request(
            request_id=request_id,
            ticket_id=ticket_id_int,
            evidence_id=evidence_id_int
        )

        return jsonify({
            'code': 200,
            'data': {
                'valid': is_valid,
                'message': message,
                'request_id': request_id,
                'ticket_id': ticket_id,
                'evidence_id': evidence_id
            }
        })

    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500


if __name__ == '__main__':
    logger.info("Starting ML Service on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)
