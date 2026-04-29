import json
import re
import math
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class Case:
    id: int
    case_no: str
    title: str
    category: str
    sub_category: Optional[str]
    description: str
    facts: str
    evidence: str
    decision: str
    decision_reason: str
    rules_applied: List[str]
    tags: List[str]
    view_count: int
    reference_count: int
    is_public: bool
    embedding: Optional[List[float]] = None


@dataclass
class MatchResult:
    case: Case
    similarity: float
    match_reasons: List[str]
    decision_alignment: str
    confidence: float


class CaseMatcher:
    def __init__(self):
        self.cases: List[Case] = self._load_default_cases()
        self.category_weights = {
            'quality': 0.35,
            'advertising': 0.30,
            'logistics': 0.20,
            'refund': 0.15
        }
        self.decision_weights = {
            'refund': 1.0,
            'return': 0.9,
            'partial_refund': 0.7,
            'seller_responsible': 0.95,
            'buyer_responsible': 0.3,
            'reject': 0.2
        }
        logger.info(f"Case Matcher initialized with {len(self.cases)} cases")

    def _load_default_cases(self) -> List[Case]:
        default_cases = [
            Case(
                id=1,
                case_no='CASE2026001',
                title='手机屏幕划痕退款案例',
                category='quality',
                sub_category='defect',
                description='买家收到手机后发现屏幕有明显划痕，申请退款',
                facts='买家提供了3张清晰的照片证据，显示屏幕存在深度划痕',
                evidence='照片证据、快递签收记录、聊天记录',
                decision='refund',
                decision_reason='证据充分，支持退款申请',
                rules_applied=['RULE_002'],
                tags=['手机', '质量问题', '划痕', '退款'],
                view_count=156,
                reference_count=23,
                is_public=True
            ),
            Case(
                id=2,
                case_no='CASE2026002',
                title='虚假宣传案例-续航能力',
                category='advertising',
                sub_category='false',
                description='商品宣传续航48小时，但实际仅12小时',
                facts='买家提供了商品宣传页截图和实际测试数据',
                evidence='宣传截图、测试视频、聊天记录',
                decision='seller_responsible',
                decision_reason='检测到虚假宣传，判定商家承担全部责任',
                rules_applied=['RULE_003'],
                tags=['虚假宣传', '续航', '商家责任', '三倍赔偿'],
                view_count=289,
                reference_count=45,
                is_public=True
            ),
            Case(
                id=3,
                case_no='CASE2026003',
                title='电子产品退货案例',
                category='refund',
                sub_category='return',
                description='买家在7天内申请无理由退货',
                facts='商品在签收后第5天申请退货，商品完好',
                evidence='快递签收记录、商品照片',
                decision='return',
                decision_reason='符合7天无理由退货条件',
                rules_applied=['RULE_001'],
                tags=['7天无理由', '退货', '电子产品'],
                view_count=98,
                reference_count=12,
                is_public=True
            ),
            Case(
                id=4,
                case_no='CASE2026004',
                title='延迟发货投诉案例',
                category='logistics',
                sub_category='late',
                description='卖家承诺48小时发货，但7天后仍未发货',
                facts='订单显示支付成功，但物流信息始终未更新',
                evidence='订单截图、聊天记录、物流查询记录',
                decision='refund',
                decision_reason='卖家未能按时发货，支持退款',
                rules_applied=['RULE_007'],
                tags=['延迟发货', '物流', '退款'],
                view_count=134,
                reference_count=18,
                is_public=True
            ),
            Case(
                id=5,
                case_no='CASE2026005',
                title='二手商品冒充新品案例',
                category='quality',
                sub_category='counterfeit',
                description='卖家宣传全新商品，但收到的是二手商品',
                facts='商品有明显使用痕迹，电池循环次数超过50次',
                evidence='商品照片、检测报告、系统信息截图',
                decision='seller_responsible',
                decision_reason='商品与描述不符，涉嫌欺诈',
                rules_applied=['RULE_003', 'RULE_009'],
                tags=['二手商品', '欺诈', '商家责任', '三倍赔偿'],
                view_count=412,
                reference_count=67,
                is_public=True
            ),
            Case(
                id=6,
                case_no='CASE2026006',
                title='价格欺诈案例',
                category='advertising',
                sub_category='price',
                description='卖家标注\"历史最低价\"但实际是日常价格',
                facts='价格走势图显示该价格已持续3个月',
                evidence='价格截图、历史价格记录、聊天记录',
                decision='partial_refund',
                decision_reason='检测到价格欺诈，支持部分退款',
                rules_applied=['RULE_008'],
                tags=['价格欺诈', '虚假宣传', '历史最低价'],
                view_count=256,
                reference_count=34,
                is_public=True
            ),
            Case(
                id=7,
                case_no='CASE2026007',
                title='买家恶意投诉案例',
                category='refund',
                sub_category='reject',
                description='买家多次投诉但证据不足',
                facts='买家无法提供有效证据证明商品问题',
                evidence='无有效证据，聊天记录显示买家试图敲诈',
                decision='reject',
                decision_reason='证据不足，驳回投诉',
                rules_applied=['RULE_010'],
                tags=['恶意投诉', '证据不足', '驳回'],
                view_count=89,
                reference_count=8,
                is_public=True
            ),
            Case(
                id=8,
                case_no='CASE2026008',
                title='客服态度恶劣案例',
                category='service',
                sub_category='rude',
                description='客服态度恶劣，拒绝提供售后服务',
                facts='聊天记录显示客服使用侮辱性语言',
                evidence='聊天记录截图、语音录音',
                decision='partial_refund',
                decision_reason='服务态度恶劣，给予部分退款补偿',
                rules_applied=['RULE_005'],
                tags=['客服态度', '服务问题', '补偿'],
                view_count=178,
                reference_count=22,
                is_public=True
            )
        ]
        return default_cases

    def match_similar_cases(
        self,
        ticket_data: Dict[str, Any],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        matches = []

        for case in self.cases:
            if not case.is_public:
                continue

            similarity, reasons = self._calculate_similarity(case, ticket_data)

            if similarity > 0.3:
                matches.append({
                    'case_id': case.id,
                    'case_no': case.case_no,
                    'title': case.title,
                    'category': case.category,
                    'sub_category': case.sub_category,
                    'decision': case.decision,
                    'decision_reason': case.decision_reason,
                    'similarity': round(similarity * 100, 1),
                    'match_reasons': reasons,
                    'view_count': case.view_count,
                    'reference_count': case.reference_count,
                    'tags': case.tags
                })

        matches.sort(key=lambda x: x['similarity'], reverse=True)
        return matches[:limit]

    def _calculate_similarity(
        self,
        case: Case,
        ticket_data: Dict[str, Any]
    ) -> tuple:
        total_score = 0.0
        max_score = 0.0
        reasons = []

        ticket_category = ticket_data.get('category', '')
        if case.category == ticket_category:
            category_weight = self.category_weights.get(case.category, 0.2)
            total_score += category_weight * 1.0
            max_score += category_weight
            reasons.append(f"类别匹配: {case.category}")

        ticket_sub_category = ticket_data.get('sub_category', '')
        if case.sub_category == ticket_sub_category:
            total_score += 0.15
            max_score += 0.15
            reasons.append(f"子类别匹配: {case.sub_category}")

        ticket_title = ticket_data.get('title', '')
        ticket_description = ticket_data.get('description', '')
        title_sim = self._text_similarity(case.title, ticket_title)
        desc_sim = self._text_similarity(case.description, ticket_description)

        text_score = (title_sim * 0.4 + desc_sim * 0.6) * 0.3
        if text_score > 0.1:
            total_score += text_score
            max_score += 0.3
            if title_sim > 0.3:
                reasons.append(f"标题相似度: {round(title_sim * 100)}%")

        ticket_type = ticket_data.get('type', '')
        ticket_decision = ticket_data.get('suggested_decision', '')

        ticket_tags = self._extract_tags(ticket_title, ticket_description)
        tag_similarity = self._tag_similarity(case.tags, ticket_tags)

        if tag_similarity > 0.2:
            total_score += tag_similarity * 0.2
            max_score += 0.2
            reasons.append(f"标签相似度: {round(tag_similarity * 100)}%")

        popularity_score = min(1.0, (case.view_count + case.reference_count * 5) / 1000) * 0.1
        total_score += popularity_score
        max_score += 0.1

        similarity = total_score / max_score if max_score > 0 else 0.0
        similarity = min(1.0, max(0.0, similarity))

        return similarity, reasons

    def _text_similarity(self, text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0

        words1 = self._tokenize(text1)
        words2 = self._tokenize(text2)

        if not words1 or not words2:
            return 0.0

        word_set = set(words1) | set(words2)
        vec1 = [words1.count(w) for w in word_set]
        vec2 = [words2.count(w) for w in word_set]

        dot_product = sum(v1 * v2 for v1, v2 in zip(vec1, vec2))
        mag1 = math.sqrt(sum(v**2 for v in vec1))
        mag2 = math.sqrt(sum(v**2 for v in vec2))

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)

    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.split()

        stop_words = {
            '的', '了', '是', '在', '有', '和', '与', '或', '这', '那',
            '一', '个', '为', '以', '上', '下', '中', '到', '从',
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on', 'at'
        }

        return [w for w in words if w not in stop_words and len(w) > 1]

    def _extract_tags(self, *texts: str) -> List[str]:
        all_text = ' '.join(texts).lower()

        tag_keywords = {
            '质量问题': ['质量', '问题', '缺陷', '损坏', '破损', '故障', '坏'],
            '虚假宣传': ['虚假', '宣传', '广告', '夸大', '欺骗', '欺诈'],
            '价格': ['价格', '低价', '贵', '便宜', '涨价', '降价', '促销'],
            '物流': ['物流', '快递', '发货', '收货', '配送', '延迟'],
            '服务': ['客服', '服务', '态度', '售后', '退款', '退货'],
            '二手': ['二手', '使用', '旧', '翻新'],
            '假货': ['假货', '假冒', '仿冒', '山寨'],
            '划痕': ['划痕', '刮痕', '擦痕', '磨痕'],
            '屏幕': ['屏幕', '显示屏', '显示', '屏幕碎', '屏幕裂'],
            '电池': ['电池', '续航', '充电', '耗电']
        }

        tags = []
        for tag, keywords in tag_keywords.items():
            for keyword in keywords:
                if keyword in all_text:
                    tags.append(tag)
                    break

        return tags

    def _tag_similarity(self, tags1: List[str], tags2: List[str]) -> float:
        if not tags1 or not tags2:
            return 0.0

        set1 = set(tags1)
        set2 = set(tags2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def search_cases(
        self,
        query: str,
        category: str = '',
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        results = []

        for case in self.cases:
            if not case.is_public:
                continue

            if category and case.category != category:
                continue

            if query:
                title_sim = self._text_similarity(query, case.title)
                desc_sim = self._text_similarity(query, case.description)
                tag_match = any(q.lower() in ' '.join(case.tags).lower() for q in query.split())

                relevance = max(title_sim, desc_sim)
                if tag_match:
                    relevance += 0.3

                if relevance < 0.1:
                    continue
            else:
                relevance = 0.5

            results.append({
                'case_id': case.id,
                'case_no': case.case_no,
                'title': case.title,
                'category': case.category,
                'sub_category': case.sub_category,
                'decision': case.decision,
                'relevance': round(relevance * 100, 1),
                'view_count': case.view_count,
                'reference_count': case.reference_count,
                'tags': case.tags
            })

        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:limit]

    def analyze_decision(
        self,
        case_data: Dict[str, Any],
        ticket_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        decision = case_data.get('decision', '')
        decision_reason = case_data.get('decision_reason', '')
        rules_applied = case_data.get('rules_applied', [])

        ticket_category = ticket_data.get('category', '')
        ticket_description = ticket_data.get('description', '')

        applicability_score = 0.0
        reasons = []

        if case_data.get('category') == ticket_category:
            applicability_score += 0.3
            reasons.append('类别匹配')

        case_tags = case_data.get('tags', [])
        ticket_tags = self._extract_tags(ticket_description)
        tag_sim = self._tag_similarity(case_tags, ticket_tags)
        applicability_score += tag_sim * 0.3

        desc_sim = self._text_similarity(
            case_data.get('description', ''),
            ticket_description
        )
        applicability_score += desc_sim * 0.4

        decision_weight = self.decision_weights.get(decision, 0.5)

        recommendation = ''
        if applicability_score > 0.7:
            recommendation = '强烈建议参考此案例'
        elif applicability_score > 0.5:
            recommendation = '建议参考此案例'
        elif applicability_score > 0.3:
            recommendation = '可参考此案例'
        else:
            recommendation = '此案例相关性较低'

        return {
            'case_decision': decision,
            'decision_reason': decision_reason,
            'rules_applied': rules_applied,
            'applicability_score': round(applicability_score * 100, 1),
            'decision_weight': decision_weight,
            'recommendation': recommendation,
            'match_reasons': reasons
        }

    def add_case(self, case_dict: Dict[str, Any]) -> None:
        case = Case(
            id=case_dict.get('id', len(self.cases) + 1),
            case_no=case_dict.get('case_no', ''),
            title=case_dict.get('title', ''),
            category=case_dict.get('category', ''),
            sub_category=case_dict.get('sub_category'),
            description=case_dict.get('description', ''),
            facts=case_dict.get('facts', ''),
            evidence=case_dict.get('evidence', ''),
            decision=case_dict.get('decision', ''),
            decision_reason=case_dict.get('decision_reason', ''),
            rules_applied=case_dict.get('rules_applied', []),
            tags=case_dict.get('tags', []),
            view_count=case_dict.get('view_count', 0),
            reference_count=case_dict.get('reference_count', 0),
            is_public=case_dict.get('is_public', True)
        )
        self.cases.append(case)
        logger.info(f"Added case: {case.case_no}")

    def get_all_cases(self) -> List[Dict[str, Any]]:
        return [
            {
                'id': c.id,
                'case_no': c.case_no,
                'title': c.title,
                'category': c.category,
                'sub_category': c.sub_category,
                'description': c.description,
                'facts': c.facts,
                'evidence': c.evidence,
                'decision': c.decision,
                'decision_reason': c.decision_reason,
                'rules_applied': c.rules_applied,
                'tags': c.tags,
                'view_count': c.view_count,
                'reference_count': c.reference_count,
                'is_public': c.is_public
            }
            for c in self.cases
        ]
