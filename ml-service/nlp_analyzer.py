import re
import math
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class NLPResult:
    sentiment: str
    sentiment_score: float
    complaint_category: str
    complaint_subcategory: str
    keywords: List[Dict[str, Any]]
    entities: List[Dict[str, Any]]
    intent: str
    urgency: str
    false_advertising_flags: List[str]
    summary: str


class NLPAnalyzer:
    def __init__(self):
        self.category_keywords = {
            'quality': {
                'keywords': ['质量', '问题', '缺陷', '损坏', '破损', '故障', '坏', '次品',
                           'scratch', 'damage', 'defect', 'broken', 'fault'],
                'subcategories': {
                    'scratch': ['划痕', '刮痕', '擦痕', '磨痕', 'scratch'],
                    'dent': ['凹陷', '凹痕', 'dent'],
                    'crack': ['裂纹', '裂缝', '开裂', '断裂', 'crack'],
                    'stain': ['污渍', '污点', '污迹', '发黄', '变色', 'stain'],
                    'function': ['无法使用', '不能用', '故障', '坏了', 'not working'],
                    'counterfeit': ['假货', '仿冒', '山寨', '假冒', 'fake', 'counterfeit']
                }
            },
            'advertising': {
                'keywords': ['虚假', '宣传', '广告', '夸大', '欺骗', '欺诈', '误导',
                           'false', 'advertising', 'misleading', 'deceptive'],
                'subcategories': {
                    'exaggerated': ['夸大', '夸张', '最好', '第一', '顶级', 'perfect', 'best'],
                    'false_claim': ['虚假', '不实', '不符', '不一致', 'false', 'not as described'],
                    'price': ['最低价', '历史最低', '价格欺诈', 'cheapest', 'price fraud'],
                    'guarantee': ['假一赔十', '100%正品', '绝对', 'guarantee', '100% authentic']
                }
            },
            'logistics': {
                'keywords': ['物流', '快递', '发货', '收货', '配送', '延迟', '丢失',
                           'logistics', 'shipping', 'delivery', 'late', 'lost'],
                'subcategories': {
                    'late': ['延迟', '晚发', '超时', '未按时', 'late', 'delayed'],
                    'lost': ['丢失', '找不到', '丢了', 'lost', 'missing'],
                    'wrong': ['发错', '发错货', '错发', 'wrong item'],
                    'missing': ['少发', '漏发', '缺少', 'missing parts']
                }
            },
            'service': {
                'keywords': ['客服', '服务', '态度', '售后', '不理', '不回复',
                           'customer service', 'attitude', 'after sales'],
                'subcategories': {
                    'rude': ['态度差', '恶劣', '骂人', '侮辱', 'rude', 'bad attitude'],
                    'ignore': ['不理人', '不回复', '无人理', 'ignore', 'no response'],
                    'refuse': ['拒绝', '不同意', '不处理', 'refuse', 'reject']
                }
            },
            'refund': {
                'keywords': ['退款', '退货', '退换', '退钱', '退款', 'refund', 'return'],
                'subcategories': {
                    'only_refund': ['仅退款', '不用退货', '不退货', 'refund only'],
                    'return_refund': ['退货退款', '退回去', '寄回', 'return and refund'],
                    'refuse_refund': ['不同意退款', '拒绝退款', '不给退', 'refuse refund']
                }
            }
        }

        self.sentiment_lexicon = {
            'positive': ['好', '棒', '满意', '愉快', '优秀', '好的', '没问题',
                        'good', 'great', 'excellent', 'satisfied', 'happy'],
            'negative': ['坏', '差', '糟糕', '失望', '生气', '愤怒', '不满意', '投诉',
                        'bad', 'poor', 'terrible', 'disappointed', 'angry', 'complaint'],
            'intensifier': ['非常', '极其', '超级', '特别', '太', 'very', 'extremely', 'super'],
            'negation': ['不', '没', '无', '非', 'not', 'no', 'never']
        }

        self.urgency_keywords = {
            'high': ['紧急', '立即', '马上', '现在', '立刻', '今天', '当天',
                    'urgent', 'immediately', 'right now', 'today'],
            'medium': ['尽快', '快点', '麻烦', '请', 'asap', 'please', 'soon'],
            'low': ['有空', '方便', '不着急', '慢慢来', 'when you can', 'no rush']
        }

        self.false_advertising_patterns = [
            (r'(?i)(最|第一|顶级|极致|完美|100%|绝对|唯一|首家|国家级|世界级)', 'absolute_claim'),
            (r'(?i)(比.*好|秒杀|完爆|无敌|最佳|最优|首选|必备|必须|强烈推荐)', 'exaggerated_comparison'),
            (r'(?i)(治疗|治愈|根治|疗效|功效|医疗|药品|抗癌|降血压|降血糖)', 'medical_claim'),
            (r'(?i)(无效退款|假一赔十|100%正品|专柜正品|原厂正品|保证正品)', 'guarantee_claim'),
            (r'(?i)(最低价|全网最低|历史最低|跳楼价|亏本甩卖|清仓大甩卖)', 'price_claim'),
            (r'(?i)(限量|限时|最后.*件|只剩.*件|倒计时|仅剩)', 'limited_claim'),
            (r'(?i)(明星推荐|明星同款|名人推荐|医生推荐|专家推荐|权威认证)', 'endorsement_claim'),
            (r'(?i)(99%|98%|95%|百分之百|百分之九十九|治愈率|有效率|满意率)', 'statistics_claim')
        ]

        self.intent_keywords = {
            'refund_request': ['退款', '退钱', '申请退款', 'refund'],
            'return_request': ['退货', '寄回', '退回', 'return'],
            'complaint': ['投诉', '举报', '差评', '不满意', 'complaint'],
            'inquiry': ['问', '查询', '了解', '怎么回事', 'ask', 'inquiry'],
            'negotiation': ['协商', '商量', '沟通', '希望', '能不能', 'negotiate']
        }

        logger.info("NLP Analyzer initialized")

    def analyze(self, text: str, analysis_type: str = 'all') -> Dict[str, Any]:
        if not text or not text.strip():
            return {
                'success': False,
                'message': 'Empty text provided'
            }

        result = {
            'success': True,
            'original_text': text,
            'analysis_type': analysis_type
        }

        if analysis_type in ['all', 'sentiment']:
            result['sentiment'] = self._analyze_sentiment(text)

        if analysis_type in ['all', 'classification']:
            result['classification'] = self._classify_complaint(text)

        if analysis_type in ['all', 'keywords']:
            result['keywords'] = self._extract_keywords(text, top_k=10)

        if analysis_type in ['all', 'intent']:
            result['intent'] = self._detect_intent(text)

        if analysis_type in ['all', 'urgency']:
            result['urgency'] = self._detect_urgency(text)

        if analysis_type in ['all', 'false_advertising']:
            result['false_advertising'] = self._detect_false_advertising(text)

        if analysis_type in ['all', 'entities']:
            result['entities'] = self._extract_entities(text)

        if analysis_type in ['all', 'summary']:
            result['summary'] = self._generate_summary(text)

        return result

    def classify_complaint(self, text: str, title: str = '') -> Dict[str, Any]:
        combined_text = f"{title} {text}".strip()
        if not combined_text:
            return {
                'category': 'unknown',
                'subcategory': 'unknown',
                'confidence': 0.0,
                'all_categories': []
            }

        category_scores = defaultdict(float)
        subcategory_scores = defaultdict(dict)

        for category, info in self.category_keywords.items():
            keywords = info['keywords']
            subcategories = info.get('subcategories', {})

            for keyword in keywords:
                count = self._count_occurrences(combined_text, keyword)
                if count > 0:
                    category_scores[category] += count * 2.0

            for subcategory, sub_keywords in subcategories.items():
                for keyword in sub_keywords:
                    count = self._count_occurrences(combined_text, keyword)
                    if count > 0:
                        category_scores[category] += count * 1.5
                        if subcategory not in subcategory_scores[category]:
                            subcategory_scores[category][subcategory] = 0
                        subcategory_scores[category][subcategory] += count

        total_score = sum(category_scores.values())
        if total_score == 0:
            return {
                'category': 'unknown',
                'subcategory': 'unknown',
                'confidence': 0.3,
                'all_categories': []
            }

        sorted_categories = sorted(
            category_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        best_category = sorted_categories[0][0]
        confidence = sorted_categories[0][1] / total_score

        best_subcategory = 'unknown'
        if best_category in subcategory_scores and subcategory_scores[best_category]:
            sorted_subcategories = sorted(
                subcategory_scores[best_category].items(),
                key=lambda x: x[1],
                reverse=True
            )
            best_subcategory = sorted_subcategories[0][0]

        all_categories = [
            {
                'category': cat,
                'score': round(score, 2),
                'percentage': round(score / total_score * 100, 1)
            }
            for cat, score in sorted_categories
        ]

        return {
            'category': best_category,
            'subcategory': best_subcategory,
            'confidence': round(confidence, 2),
            'all_categories': all_categories,
            'category_names': {
                'quality': '质量问题',
                'advertising': '宣传问题',
                'logistics': '物流问题',
                'service': '服务问题',
                'refund': '退款退货'
            }
        }

    def _count_occurrences(self, text: str, keyword: str) -> int:
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        return text_lower.count(keyword_lower)

    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        words = self._tokenize(text)

        positive_count = 0
        negative_count = 0
        intensifier_multiplier = 1.0
        negation_active = False

        for word in words:
            word_lower = word.lower()

            if word_lower in self.sentiment_lexicon['intensifier']:
                intensifier_multiplier = 1.5
                continue

            if word_lower in self.sentiment_lexicon['negation']:
                negation_active = True
                continue

            score = 1.0 * intensifier_multiplier
            if negation_active:
                score = -score

            if word_lower in self.sentiment_lexicon['positive']:
                positive_count += score
            elif word_lower in self.sentiment_lexicon['negative']:
                negative_count += score

            intensifier_multiplier = 1.0
            negation_active = False

        total = positive_count + negative_count
        if total == 0:
            sentiment = 'neutral'
            score = 0.5
        else:
            score = positive_count / total
            if score > 0.6:
                sentiment = 'positive'
            elif score < 0.4:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'

        return {
            'sentiment': sentiment,
            'score': round(score, 2),
            'positive_count': round(positive_count, 1),
            'negative_count': round(negative_count, 1),
            'sentiment_names': {
                'positive': '正面',
                'negative': '负面',
                'neutral': '中性'
            }
        }

    def _tokenize(self, text: str) -> List[str]:
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.split()
        return [w for w in words if len(w) > 0]

    def _extract_keywords(self, text: str, top_k: int = 10) -> List[Dict[str, Any]]:
        words = self._tokenize(text)

        stop_words = {
            '的', '了', '是', '在', '有', '和', '与', '或', '这', '那',
            '一', '个', '为', '以', '上', '下', '中', '到', '从', '我',
            '你', '他', '她', '它', '们', '就', '也', '都', '还', '又',
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on', 'at',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'and', 'or', 'but'
        }

        word_freq = Counter()
        for word in words:
            word_lower = word.lower()
            if word_lower not in stop_words and len(word_lower) > 1:
                word_freq[word_lower] += 1

        total_words = sum(word_freq.values())
        tfidf_scores = {}

        for word, freq in word_freq.items():
            tf = freq / total_words if total_words > 0 else 0
            category_boost = 0
            for category, info in self.category_keywords.items():
                if word in [k.lower() for k in info['keywords']]:
                    category_boost += 0.2
                for sub_keywords in info.get('subcategories', {}).values():
                    if word in [k.lower() for k in sub_keywords]:
                        category_boost += 0.3
            tfidf_scores[word] = tf * (1 + category_boost)

        sorted_keywords = sorted(
            tfidf_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]

        result = []
        for word, score in sorted_keywords:
            result.append({
                'word': word,
                'score': round(score, 4),
                'frequency': word_freq[word]
            })

        return result

    def _detect_intent(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()

        intent_scores = defaultdict(int)

        for intent, keywords in self.intent_keywords.items():
            for keyword in keywords:
                count = self._count_occurrences(text_lower, keyword)
                if count > 0:
                    intent_scores[intent] += count

        if not intent_scores:
            return {
                'intent': 'unknown',
                'confidence': 0.3,
                'all_intents': []
            }

        total = sum(intent_scores.values())
        sorted_intents = sorted(
            intent_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        best_intent = sorted_intents[0][0]
        confidence = sorted_intents[0][1] / total

        all_intents = [
            {
                'intent': intent,
                'score': score,
                'percentage': round(score / total * 100, 1)
            }
            for intent, score in sorted_intents
        ]

        return {
            'intent': best_intent,
            'confidence': round(confidence, 2),
            'all_intents': all_intents,
            'intent_names': {
                'refund_request': '退款请求',
                'return_request': '退货请求',
                'complaint': '投诉',
                'inquiry': '咨询',
                'negotiation': '协商'
            }
        }

    def _detect_urgency(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()

        high_count = 0
        medium_count = 0
        low_count = 0

        for keyword in self.urgency_keywords['high']:
            high_count += self._count_occurrences(text_lower, keyword)

        for keyword in self.urgency_keywords['medium']:
            medium_count += self._count_occurrences(text_lower, keyword)

        for keyword in self.urgency_keywords['low']:
            low_count += self._count_occurrences(text_lower, keyword)

        if high_count > 0:
            urgency = 'high'
            score = 0.8 + (high_count * 0.05)
        elif medium_count > 0:
            urgency = 'medium'
            score = 0.5 + (medium_count * 0.05)
        elif low_count > 0:
            urgency = 'low'
            score = 0.2 + (low_count * 0.05)
        else:
            urgency = 'medium'
            score = 0.5

        return {
            'urgency': urgency,
            'score': round(min(1.0, score), 2),
            'urgency_names': {
                'high': '高',
                'medium': '中',
                'low': '低'
            }
        }

    def _detect_false_advertising(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()

        detected_patterns = []

        for pattern, pattern_type in self.false_advertising_patterns:
            matches = re.findall(pattern, text)
            if matches:
                detected_patterns.append({
                    'type': pattern_type,
                    'matches': list(set(matches)),
                    'count': len(matches)
                })

        has_false_claim = len(detected_patterns) > 0

        severity = 'low'
        if has_false_claim:
            total_count = sum(p['count'] for p in detected_patterns)
            if total_count >= 3:
                severity = 'high'
            elif total_count >= 2:
                severity = 'medium'
            else:
                high_risk_types = ['absolute_claim', 'medical_claim', 'guarantee_claim']
                if any(p['type'] in high_risk_types for p in detected_patterns):
                    severity = 'high'

        return {
            'has_false_claim': has_false_claim,
            'severity': severity,
            'detected_patterns': detected_patterns,
            'pattern_names': {
                'absolute_claim': '绝对化宣传',
                'exaggerated_comparison': '夸大对比',
                'medical_claim': '医疗功效宣称',
                'guarantee_claim': '保证性承诺',
                'price_claim': '价格承诺',
                'limited_claim': '限量限时宣传',
                'endorsement_claim': '名人/专家推荐',
                'statistics_claim': '统计数据宣称'
            },
            'severity_names': {
                'low': '轻度',
                'medium': '中度',
                'high': '重度'
            }
        }

    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        entities = []

        money_pattern = r'(\d+(?:\.\d+)?)\s*[元块$￥]'
        money_matches = re.findall(money_pattern, text)
        for match in money_matches:
            entities.append({
                'type': 'money',
                'value': float(match),
                'text': match,
                'entity_name': '金额'
            })

        order_pattern = r'(?:订单|order|ORD)[\s#-]*([A-Za-z0-9]+)'
        order_matches = re.findall(order_pattern, text, re.IGNORECASE)
        for match in order_matches:
            entities.append({
                'type': 'order_number',
                'value': match,
                'text': match,
                'entity_name': '订单号'
            })

        phone_pattern = r'1[3-9]\d{9}'
        phone_matches = re.findall(phone_pattern, text)
        for match in phone_matches:
            entities.append({
                'type': 'phone',
                'value': match,
                'text': match,
                'entity_name': '电话号码'
            })

        time_pattern = r'(\d+(?:\.\d+)?)\s*(?:天|日|小时|钟头|h|hour)'
        time_matches = re.findall(time_pattern, text)
        for match in time_matches:
            entities.append({
                'type': 'time',
                'value': float(match),
                'text': match,
                'entity_name': '时间'
            })

        return entities

    def _generate_summary(self, text: str, max_length: int = 100) -> str:
        if len(text) <= max_length:
            return text

        sentences = re.split(r'[。！？.!?]', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return text[:max_length] + '...'

        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = 0

            if i == 0:
                score += 0.3

            for category, info in self.category_keywords.items():
                for keyword in info['keywords']:
                    if keyword in sentence:
                        score += 0.2

            for keyword in self.sentiment_lexicon['negative']:
                if keyword in sentence:
                    score += 0.1

            scored_sentences.append((sentence, score, i))

        scored_sentences.sort(key=lambda x: (x[1], -x[2]), reverse=True)

        top_sentences = scored_sentences[:2]
        top_sentences.sort(key=lambda x: x[2])

        summary = ''.join(f"{s[0]}。" for s in top_sentences)

        if len(summary) > max_length:
            summary = summary[:max_length] + '...'

        return summary

    def extract_keywords(self, text: str, top_k: int = 10) -> Dict[str, Any]:
        keywords = self._extract_keywords(text, top_k)
        return {
            'keywords': keywords,
            'count': len(keywords)
        }
