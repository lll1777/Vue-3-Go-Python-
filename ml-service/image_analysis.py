import os
import re
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

try:
    from PIL import Image, ImageEnhance, ImageFilter
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    logger.warning("PIL not installed, using mock analysis")

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False
    logger.warning("pytesseract not installed, text extraction disabled")


class IssueType(Enum):
    SCRATCH = "scratch"
    DENT = "dent"
    CRACK = "crack"
    STAIN = "stain"
    MISSING_PART = "missing_part"
    DEFECT = "defect"
    USED_PRODUCT = "used_product"
    PACKAGE_DAMAGED = "package_damaged"


class FalseClaimType(Enum):
    EXAGGERATED_FEATURE = "exaggerated_feature"
    FALSE_PRICE = "false_price"
    MISLEADING_DESCRIPTION = "misleading_description"
    FAKE_REVIEW = "fake_review"
    COUNTERFEIT = "counterfeit"
    UNAUTHORIZED_BRAND = "unauthorized_brand"


@dataclass
class ImageAnalysisResult:
    has_issue: bool
    issue_type: Optional[str]
    confidence: float
    description: str
    details: Dict[str, Any]
    text_extracted: str
    has_false_claim: bool
    false_claim_type: Optional[str]
    used_product: bool
    quality_score: float


class ImageAnalyzer:
    def __init__(self):
        self.false_claim_keywords = {
            'absolute': r'(?i)(最|第一|顶级|极致|完美|100%|绝对|唯一|首家|国家级|世界级)',
            'exaggerated': r'(?i)(比.*好|秒杀|完爆|无敌|最佳|最优|首选|必备|必须|强烈推荐)',
            'medical': r'(?i)(治疗|治愈|根治|疗效|功效|医疗|药品|抗癌|降血压|降血糖)',
            'guarantee': r'(?i)(无效退款|假一赔十|100%正品|专柜正品|原厂正品)',
            'price': r'(?i)(最低价|全网最低|历史最低|跳楼价|亏本甩卖|清仓)',
            'limited': r'(?i)(限量|限时|最后.*件|只剩.*件|倒计时)',
            'celebrity': r'(?i)(明星推荐|明星同款|名人推荐|医生推荐|专家推荐)',
            'statistics': r'(?i)(99%|98%|95%|百分之百|百分之九十九|治愈率|有效率|满意率)'
        }

        self.quality_indicators = {
            'scratch': ['划痕', '刮痕', '磨痕', '擦痕', 'scratch', 'scuff'],
            'dent': ['凹陷', '凹痕', '凸凹', 'dent', 'indentation'],
            'crack': ['裂纹', '裂缝', '开裂', '断裂', 'crack', 'broken'],
            'stain': ['污渍', '污点', '污迹', '发黄', '变色', 'stain', 'discoloration'],
            'missing': ['缺少', '缺失', '漏发', '没有', 'missing', 'absent'],
            'used': ['二手', '使用过', '旧的', '磨损', '折旧', 'used', 'worn', 'second-hand'],
            'package': ['包装破损', '盒子坏了', '包装损坏', '包装压坏']
        }

        logger.info("Image Analyzer initialized")

    def analyze(self, image_path: str, analysis_type: str = 'all') -> Dict[str, Any]:
        result = {
            'image_path': image_path,
            'analysis_type': analysis_type,
            'success': True,
            'image_analysis': None,
            'text_analysis': None
        }

        try:
            if not HAS_PIL:
                result['image_analysis'] = self._mock_image_analysis(image_path)
                result['text_analysis'] = self._mock_text_analysis(image_path)
                return result

            image = Image.open(image_path)
            image_info = self._get_image_info(image)

            if analysis_type in ['all', 'quality']:
                result['image_analysis'] = self._analyze_quality(image, image_path)

            if analysis_type in ['all', 'text', 'false_advertising']:
                extracted_text = self._extract_text(image, image_path)
                result['text_analysis'] = self._analyze_text(extracted_text)

            if analysis_type in ['all', 'false_advertising']:
                result['false_advertising'] = self._detect_false_advertising_from_analysis(
                    result.get('image_analysis', {}),
                    result.get('text_analysis', {})
                )

        except Exception as e:
            logger.error(f"Image analysis error: {str(e)}")
            result['success'] = False
            result['error'] = str(e)

        return result

    def _get_image_info(self, image: 'Image.Image') -> Dict[str, Any]:
        return {
            'size': image.size,
            'mode': image.mode,
            'format': image.format,
            'width': image.width,
            'height': image.height
        }

    def _analyze_quality(self, image: 'Image.Image', image_path: str) -> Dict[str, Any]:
        try:
            gray_image = image.convert('L')
            edges = self._detect_edges(gray_image)
            contrast = self._analyze_contrast(gray_image)
            color_consistency = self._analyze_color_consistency(image)

            has_issue = False
            issue_type = None
            confidence = 0.0
            quality_score = 1.0

            if edges > 0.3:
                has_issue = True
                issue_type = 'scratch_or_crack'
                confidence = min(0.9, edges * 2)
                quality_score = max(0.3, 1 - edges)

            if color_consistency < 0.7:
                has_issue = True
                issue_type = issue_type or 'discoloration'
                confidence = max(confidence, 1 - color_consistency)
                quality_score = min(quality_score, color_consistency)

            used_product = self._detect_used_product(image)
            if used_product:
                has_issue = True
                issue_type = 'used_product'
                confidence = max(confidence, 0.85)
                quality_score = min(quality_score, 0.5)

            return {
                'has_issue': has_issue,
                'issue_type': issue_type,
                'confidence': float(confidence),
                'quality_score': float(quality_score),
                'used_product': used_product,
                'edge_density': float(edges),
                'contrast_score': float(contrast),
                'color_consistency': float(color_consistency)
            }

        except Exception as e:
            logger.error(f"Quality analysis error: {e}")
            return self._mock_image_analysis(image_path)

    def _detect_edges(self, gray_image: 'Image.Image') -> float:
        try:
            edges = gray_image.filter(ImageFilter.FIND_EDGES)
            edge_pixels = sum(1 for p in edges.getdata() if p > 50)
            total_pixels = gray_image.width * gray_image.height
            return edge_pixels / total_pixels
        except:
            return 0.1

    def _analyze_contrast(self, gray_image: 'Image.Image') -> float:
        try:
            data = list(gray_image.getdata())
            if not data:
                return 0.5

            max_val = max(data)
            min_val = min(data)
            contrast = (max_val - min_val) / 255.0 if max_val != min_val else 0
            return contrast
        except:
            return 0.5

    def _analyze_color_consistency(self, image: 'Image.Image') -> float:
        try:
            if image.mode != 'RGB':
                image = image.convert('RGB')

            width, height = image.size
            sample_size = min(width, height) // 4

            regions = [
                image.crop((0, 0, sample_size, sample_size)),
                image.crop((width - sample_size, 0, width, sample_size)),
                image.crop((0, height - sample_size, sample_size, height)),
                image.crop((width - sample_size, height - sample_size, width, height)),
                image.crop((width // 2 - sample_size // 2, height // 2 - sample_size // 2,
                           width // 2 + sample_size // 2, height // 2 + sample_size // 2))
            ]

            region_colors = []
            for region in regions:
                r, g, b = 0, 0, 0
                pixels = list(region.getdata())
                for pixel in pixels:
                    r += pixel[0]
                    g += pixel[1]
                    b += pixel[2]
                n = len(pixels)
                region_colors.append((r // n, g // n, b // n))

            if len(region_colors) < 2:
                return 1.0

            max_diff = 0
            for i in range(len(region_colors)):
                for j in range(i + 1, len(region_colors)):
                    c1, c2 = region_colors[i], region_colors[j]
                    diff = ((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2 + (c1[2] - c2[2])**2)**0.5
                    max_diff = max(max_diff, diff)

            consistency = 1 - (max_diff / (255 * (3**0.5)))
            return max(0, min(1, consistency))

        except:
            return 0.8

    def _detect_used_product(self, image: 'Image.Image') -> bool:
        try:
            edges = self._detect_edges(image.convert('L'))
            contrast = self._analyze_contrast(image.convert('L'))

            if edges > 0.4 or contrast > 0.8:
                return True

            return False
        except:
            return False

    def _extract_text(self, image: 'Image.Image', image_path: str) -> str:
        if not HAS_TESSERACT:
            return self._mock_text_extraction(image_path)

        try:
            text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            return text.strip()
        except Exception as e:
            logger.warning(f"OCR error: {e}")
            return self._mock_text_extraction(image_path)

    def _analyze_text(self, text: str) -> Dict[str, Any]:
        if not text:
            return {
                'has_false_claim': False,
                'false_advertising': False,
                'price_fraud': False,
                'extracted_text': '',
                'detected_keywords': [],
                'analysis_score': 1.0
            }

        detected_keywords = []
        has_false_claim = False
        false_advertising = False
        price_fraud = False

        for category, pattern in self.false_claim_keywords.items():
            matches = re.findall(pattern, text)
            if matches:
                detected_keywords.append({
                    'category': category,
                    'matches': matches,
                    'count': len(matches)
                })
                has_false_claim = True

                if category in ['absolute', 'exaggerated', 'guarantee', 'medical']:
                    false_advertising = True
                if category == 'price':
                    price_fraud = True

        quality_issues = []
        for issue_type, indicators in self.quality_indicators.items():
            for indicator in indicators:
                if indicator in text or (isinstance(indicator, str) and indicator.lower() in text.lower()):
                    quality_issues.append({
                        'type': issue_type,
                        'indicator': indicator
                    })
                    break

        analysis_score = 1.0
        if has_false_claim:
            analysis_score -= 0.3 * len(detected_keywords)
        if quality_issues:
            analysis_score -= 0.2 * len(quality_issues)

        analysis_score = max(0, min(1, analysis_score))

        return {
            'has_false_claim': has_false_claim,
            'false_advertising': false_advertising,
            'price_fraud': price_fraud,
            'extracted_text': text,
            'detected_keywords': detected_keywords,
            'quality_issues': quality_issues,
            'analysis_score': analysis_score
        }

    def _detect_false_advertising_from_analysis(
        self,
        image_analysis: Dict,
        text_analysis: Dict
    ) -> Dict[str, Any]:
        has_false_claim = False
        false_claim_type = None
        confidence = 0.0

        if text_analysis and text_analysis.get('has_false_claim'):
            has_false_claim = True
            keywords = text_analysis.get('detected_keywords', [])

            for kw in keywords:
                if kw['category'] == 'absolute':
                    false_claim_type = 'exaggerated_feature'
                    confidence = max(confidence, 0.9)
                elif kw['category'] == 'price':
                    false_claim_type = 'false_price'
                    confidence = max(confidence, 0.85)
                elif kw['category'] == 'guarantee':
                    false_claim_type = 'misleading_description'
                    confidence = max(confidence, 0.8)

        if image_analysis and image_analysis.get('used_product'):
            has_false_claim = True
            false_claim_type = false_claim_type or 'counterfeit'
            confidence = max(confidence, 0.85)

        return {
            'has_false_claim': has_false_claim,
            'false_claim_type': false_claim_type,
            'confidence': confidence,
            'recommendation': '建议进一步核实' if has_false_claim else '未检测到虚假宣传'
        }

    def detect_false_advertising(
        self,
        image_path: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        result = self.analyze(image_path, 'false_advertising')

        false_analysis = result.get('false_advertising', {})
        text_analysis = result.get('text_analysis', {})

        if context:
            context_analysis = self._analyze_text(context)
            if context_analysis.get('has_false_claim'):
                false_analysis['has_false_claim'] = True
                false_analysis['context_keywords'] = context_analysis.get('detected_keywords', [])

        return {
            'has_false_claim': false_analysis.get('has_false_claim', False),
            'false_claim_type': false_analysis.get('false_claim_type'),
            'confidence': false_analysis.get('confidence', 0.0),
            'extracted_text': text_analysis.get('extracted_text', ''),
            'detected_keywords': text_analysis.get('detected_keywords', []),
            'recommendation': false_analysis.get('recommendation', ''),
            'context_analysis': context_analysis if context else None
        }

    def detect_quality_issues(self, image_path: str) -> Dict[str, Any]:
        result = self.analyze(image_path, 'quality')
        image_analysis = result.get('image_analysis', {})

        issues = []
        if image_analysis.get('has_issue'):
            issue_type = image_analysis.get('issue_type', 'unknown')
            issues.append({
                'type': issue_type,
                'confidence': image_analysis.get('confidence', 0),
                'description': self._get_issue_description(issue_type)
            })

        return {
            'has_issue': image_analysis.get('has_issue', False),
            'issues': issues,
            'quality_score': image_analysis.get('quality_score', 1.0),
            'used_product': image_analysis.get('used_product', False),
            'analysis_details': {
                'edge_density': image_analysis.get('edge_density'),
                'contrast_score': image_analysis.get('contrast_score'),
                'color_consistency': image_analysis.get('color_consistency')
            }
        }

    def _get_issue_description(self, issue_type: str) -> str:
        descriptions = {
            'scratch_or_crack': '检测到表面可能存在划痕或裂纹',
            'discoloration': '检测到颜色不一致，可能存在污渍或变色',
            'used_product': '检测到商品可能为二手商品或有使用痕迹',
            'unknown': '检测到质量问题，但无法确定具体类型'
        }
        return descriptions.get(issue_type, '检测到质量问题')

    def _mock_image_analysis(self, image_path: str) -> Dict[str, Any]:
        filename = os.path.basename(image_path).lower()

        has_issue = False
        issue_type = None
        confidence = 0.0
        used_product = False

        issue_keywords = ['scratch', 'damage', 'defect', 'broken', 'used', 'second-hand',
                          '划痕', '破损', '缺陷', '二手', '旧', '损坏']

        for kw in issue_keywords:
            if kw in filename:
                has_issue = True
                if kw in ['used', 'second-hand', '二手', '旧']:
                    used_product = True
                    issue_type = 'used_product'
                else:
                    issue_type = 'defect'
                confidence = 0.85
                break

        import random
        if not has_issue and random.random() < 0.15:
            has_issue = random.choice([True, False])
            if has_issue:
                issue_type = random.choice(['scratch', 'dent', 'stain'])
                confidence = random.uniform(0.6, 0.9)

        return {
            'has_issue': has_issue,
            'issue_type': issue_type,
            'confidence': float(confidence),
            'quality_score': float(1 - confidence * 0.5) if has_issue else 0.95,
            'used_product': used_product,
            'edge_density': 0.15 if not has_issue else 0.45,
            'contrast_score': 0.65,
            'color_consistency': 0.85 if not has_issue else 0.55
        }

    def _mock_text_analysis(self, image_path: str) -> Dict[str, Any]:
        filename = os.path.basename(image_path).lower()

        has_false_claim = False
        false_advertising = False
        price_fraud = False
        detected_keywords = []

        false_keywords = {
            '绝对': 'absolute', '最好': 'exaggerated', '第一': 'absolute',
            '100%': 'guarantee', '正品': 'guarantee', '最低价': 'price',
            'limited': 'limited', '限量': 'limited',
            'best': 'exaggerated', 'perfect': 'absolute', 'cheapest': 'price'
        }

        for kw, category in false_keywords.items():
            if kw in filename:
                has_false_claim = True
                detected_keywords.append({
                    'category': category,
                    'matches': [kw],
                    'count': 1
                })

                if category in ['absolute', 'exaggerated']:
                    false_advertising = True
                if category == 'price':
                    price_fraud = True

        extracted_text = self._mock_text_extraction(image_path)

        return {
            'has_false_claim': has_false_claim,
            'false_advertising': false_advertising,
            'price_fraud': price_fraud,
            'extracted_text': extracted_text,
            'detected_keywords': detected_keywords,
            'quality_issues': [],
            'analysis_score': 0.7 if has_false_claim else 0.95
        }

    def _mock_text_extraction(self, image_path: str) -> str:
        mock_texts = [
            "",
            "本商品采用最新技术，性能提升50%，绝对是行业第一！",
            "限时促销，全网最低价，假一赔十！",
            "明星推荐，医生认证，治愈率高达98%！",
            "优质商品，品质保证，七天无理由退换"
        ]

        import random
        return random.choice(mock_texts)
