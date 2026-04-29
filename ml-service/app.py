from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import logging

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


if __name__ == '__main__':
    logger.info("Starting ML Service on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)
