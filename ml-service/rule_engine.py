import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DecisionType(Enum):
    REFUND = "refund"
    RETURN = "return"
    REJECT = "reject"
    SELLER_RESPONSIBLE = "seller_responsible"
    BUYER_RESPONSIBLE = "buyer_responsible"
    PARTIAL_REFUND = "partial_refund"
    PENDING = "pending"


@dataclass
class Rule:
    id: int
    name: str
    code: str
    category: str
    description: str
    conditions: str
    actions: str
    priority: int = 50
    weight: int = 100
    is_active: bool = True
    version: int = 1


@dataclass
class EvaluationResult:
    decision: str
    confidence: int
    reason: str
    matched_rules: List[Dict] = field(default_factory=list)
    details: Dict = field(default_factory=dict)
    suggested_action: str = ""


class RuleEngine:
    def __init__(self):
        self.rules: List[Rule] = self._load_default_rules()
        logger.info("Rule Engine initialized with default rules")

    def _load_default_rules(self) -> List[Rule]:
        default_rules = [
            Rule(
                id=1,
                name="7天无理由退货",
                code="RULE_001",
                category="refund",
                description="商品在7天退货期限内，支持无理由退货",
                conditions=json.dumps({
                    "type": "return",
                    "days_since_receive": {"$lte": 7},
                    "product_condition": "good"
                }),
                actions=json.dumps({
                    "decision": "return",
                    "reason": "7天无理由退货",
                    "weight_bonus": 10
                }),
                priority=100,
                weight=100
            ),
            Rule(
                id=2,
                name="质量问题退款",
                code="RULE_002",
                category="quality",
                description="图片证据显示存在明确质量问题，支持退款",
                conditions=json.dumps({
                    "image_analysis.has_issue": True,
                    "evidence_count": {"$gte": 1},
                    "category": ["quality", "defect"]
                }),
                actions=json.dumps({
                    "decision": "refund",
                    "reason": "质量问题证据充分",
                    "weight_bonus": 20
                }),
                priority=90,
                weight=95
            ),
            Rule(
                id=3,
                name="虚假宣传判定",
                code="RULE_003",
                category="advertising",
                description="检测到虚假宣传内容，判定商家责任",
                conditions=json.dumps({
                    "image_analysis.has_false_claim": True,
                    "category": "advertising",
                    "text_analysis.false_advertising": True
                }),
                actions=json.dumps({
                    "decision": "seller_responsible",
                    "reason": "虚假宣传",
                    "weight_bonus": 25,
                    "seller_score_penalty": 5
                }),
                priority=95,
                weight=98
            ),
            Rule(
                id=4,
                name="商家超时响应",
                code="RULE_004",
                category="sla",
                description="商家在协商期内未响应，自动支持买家诉求",
                conditions=json.dumps({
                    "stage": "negotiation",
                    "sla_percentage": {"$gte": 100},
                    "seller_response_count": 0
                }),
                actions=json.dumps({
                    "decision": "refund",
                    "reason": "商家超时未响应",
                    "weight_bonus": 15,
                    "seller_score_penalty": 2
                }),
                priority=80,
                weight=90
            ),
            Rule(
                id=5,
                name="商家服务分低于阈值",
                code="RULE_005",
                category="seller_score",
                description="商家服务分低于70分，增加买家胜诉权重",
                conditions=json.dumps({
                    "seller_service_score": {"$lt": 70}
                }),
                actions=json.dumps({
                    "decision": None,
                    "reason": "商家服务分过低",
                    "weight_adjust": 20,
                    "buyer_weight_bonus": 15
                }),
                priority=70,
                weight=75
            ),
            Rule(
                id=6,
                name="买家信誉良好",
                code="RULE_006",
                category="buyer_credit",
                description="买家信誉分高于90分，增加胜诉权重",
                conditions=json.dumps({
                    "buyer_credit_score": {"$gte": 90},
                    "buyer_dispute_win_rate": {"$gte": 0.7}
                }),
                actions=json.dumps({
                    "decision": None,
                    "reason": "买家信誉良好",
                    "weight_adjust": 10,
                    "buyer_weight_bonus": 10
                }),
                priority=60,
                weight=70
            ),
            Rule(
                id=7,
                name="物流问题判定",
                code="RULE_007",
                category="logistics",
                description="物流问题导致的纠纷，支持买家",
                conditions=json.dumps({
                    "category": "logistics",
                    "sub_category": ["late", "lost", "wrong", "missing"]
                }),
                actions=json.dumps({
                    "decision": "refund",
                    "reason": "物流问题",
                    "weight_bonus": 15
                }),
                priority=85,
                weight=85
            ),
            Rule(
                id=8,
                name="价格欺诈判定",
                code="RULE_008",
                category="advertising",
                description="检测到价格欺诈，判定商家责任",
                conditions=json.dumps({
                    "category": "advertising",
                    "sub_category": "price",
                    "text_analysis.price_fraud": True
                }),
                actions=json.dumps({
                    "decision": "seller_responsible",
                    "reason": "价格欺诈",
                    "weight_bonus": 30,
                    "seller_score_penalty": 10,
                    "triple_damages": True
                }),
                priority=100,
                weight=100
            ),
            Rule(
                id=9,
                name="二手商品问题",
                code="RULE_009",
                category="quality",
                description="检测到商品为二手或有使用痕迹",
                conditions=json.dumps({
                    "image_analysis.used_product": True,
                    "product_condition": "used",
                    "seller_claimed_new": True
                }),
                actions=json.dumps({
                    "decision": "refund",
                    "reason": "商品与描述不符（二手商品）",
                    "weight_bonus": 20
                }),
                priority=90,
                weight=90
            ),
            Rule(
                id=10,
                name="重复投诉低信用买家",
                code="RULE_010",
                category="buyer_credit",
                description="买家历史投诉过多且胜率低，降低权重",
                conditions=json.dumps({
                    "buyer_credit_score": {"$lt": 60},
                    "buyer_dispute_count": {"$gte": 5},
                    "buyer_dispute_win_rate": {"$lt": 0.3}
                }),
                actions=json.dumps({
                    "decision": None,
                    "reason": "买家历史纠纷记录异常",
                    "weight_adjust": -15,
                    "seller_weight_bonus": 10
                }),
                priority=75,
                weight=65
            )
        ]
        return default_rules

    def evaluate(
        self,
        ticket_data: Dict[str, Any],
        evidences: List[Dict],
        rules: Optional[List[Dict]] = None
    ) -> EvaluationResult:
        if rules:
            active_rules = [self._dict_to_rule(r) for r in rules if r.get('is_active', True)]
        else:
            active_rules = [r for r in self.rules if r.is_active]

        active_rules.sort(key=lambda x: x.priority, reverse=True)

        matched_rules = []
        total_weight = 0
        decision_weights = {}
        weight_adjustments = {'buyer': 0, 'seller': 0}

        for rule in active_rules:
            match_result = self._check_condition(rule, ticket_data, evidences)
            if match_result:
                matched_rules.append({
                    'id': rule.id,
                    'name': rule.name,
                    'code': rule.code,
                    'category': rule.category,
                    'weight': rule.weight,
                    'priority': rule.priority
                })
                total_weight += rule.weight

                actions = json.loads(rule.actions)
                decision = actions.get('decision')
                weight_bonus = actions.get('weight_bonus', 0)
                weight_adjust = actions.get('weight_adjust', 0)
                buyer_weight_bonus = actions.get('buyer_weight_bonus', 0)
                seller_weight_bonus = actions.get('seller_weight_bonus', 0)

                if decision:
                    if decision not in decision_weights:
                        decision_weights[decision] = 0
                    decision_weights[decision] += rule.weight + weight_bonus

                if weight_adjust:
                    weight_adjustments['buyer'] += weight_adjust

                if buyer_weight_bonus:
                    weight_adjustments['buyer'] += buyer_weight_bonus

                if seller_weight_bonus:
                    weight_adjustments['seller'] += seller_weight_bonus

        final_decision = DecisionType.PENDING.value
        confidence = 0
        reason = "证据不足，等待更多信息"

        if matched_rules:
            if decision_weights:
                max_decision = max(decision_weights.keys(), key=lambda k: decision_weights[k])
                max_weight = decision_weights[max_decision]

                buyer_advantage = weight_adjustments['buyer'] - weight_adjustments['seller']
                adjusted_weight = max_weight + buyer_advantage
                adjusted_total = total_weight + abs(buyer_advantage)

                if adjusted_total > 0:
                    confidence = int((adjusted_weight / adjusted_total) * 100)
                else:
                    confidence = 50

                final_decision = max_decision
                reason = f"匹配到 {len(matched_rules)} 条规则，置信度 {confidence}%"

                if confidence >= 80:
                    reason += "，建议采纳"
                elif confidence >= 60:
                    reason += "，建议参考"
                else:
                    reason += "，建议人工仲裁"

        return EvaluationResult(
            decision=final_decision,
            confidence=confidence,
            reason=reason,
            matched_rules=matched_rules,
            details={
                'decision_weights': decision_weights,
                'weight_adjustments': weight_adjustments,
                'total_weight': total_weight
            },
            suggested_action=self._get_suggested_action(final_decision, confidence)
        )

    def _check_condition(
        self,
        rule: Rule,
        ticket_data: Dict[str, Any],
        evidences: List[Dict]
    ) -> bool:
        try:
            conditions = json.loads(rule.conditions)
            return self._evaluate_conditions(conditions, ticket_data, evidences)
        except Exception as e:
            logger.error(f"Error checking rule {rule.code}: {e}")
            return False

    def _evaluate_conditions(
        self,
        conditions: Dict,
        ticket_data: Dict,
        evidences: List[Dict]
    ) -> bool:
        for key, value in conditions.items():
            if isinstance(value, dict):
                if not self._evaluate_operator(key, value, ticket_data, evidences):
                    return False
            else:
                if not self._evaluate_equals(key, value, ticket_data, evidences):
                    return False
        return True

    def _evaluate_operator(
        self,
        key: str,
        operator_dict: Dict,
        ticket_data: Dict,
        evidences: List[Dict]
    ) -> bool:
        actual_value = self._get_nested_value(key, ticket_data, evidences)

        for operator, expected_value in operator_dict.items():
            if operator == '$gte':
                if actual_value is None or actual_value < expected_value:
                    return False
            elif operator == '$lte':
                if actual_value is None or actual_value > expected_value:
                    return False
            elif operator == '$gt':
                if actual_value is None or actual_value <= expected_value:
                    return False
            elif operator == '$lt':
                if actual_value is None or actual_value >= expected_value:
                    return False
            elif operator == '$eq':
                if actual_value != expected_value:
                    return False
            elif operator == '$ne':
                if actual_value == expected_value:
                    return False
            elif operator == '$in':
                if isinstance(expected_value, list):
                    if actual_value not in expected_value:
                        return False
                else:
                    if actual_value != expected_value:
                        return False

        return True

    def _evaluate_equals(
        self,
        key: str,
        expected_value: Any,
        ticket_data: Dict,
        evidences: List[Dict]
    ) -> bool:
        actual_value = self._get_nested_value(key, ticket_data, evidences)

        if isinstance(expected_value, list):
            return actual_value in expected_value
        return actual_value == expected_value

    def _get_nested_value(
        self,
        key: str,
        ticket_data: Dict,
        evidences: List[Dict]
    ) -> Any:
        keys = key.split('.')

        if key == 'evidence_count':
            return len(evidences)

        if key.startswith('image_analysis') or key.startswith('text_analysis'):
            return self._get_analysis_value(key, evidences)

        data = ticket_data
        for k in keys:
            if isinstance(data, dict):
                data = data.get(k)
            else:
                return None
            if data is None:
                return None

        return data

    def _get_analysis_value(self, key: str, evidences: List[Dict]) -> Any:
        parts = key.split('.')
        if len(parts) < 2:
            return None

        analysis_type = parts[1]

        for evidence in evidences:
            analysis = evidence.get('analysis', {})
            if analysis_type in ['has_issue', 'issue_type', 'confidence', 'used_product']:
                analysis_result = analysis.get('image_analysis', {})
                if analysis_type == 'has_issue':
                    return analysis_result.get('has_issue', False)
                elif analysis_type == 'used_product':
                    return analysis_result.get('used_product', False)
                elif analysis_type == 'confidence':
                    return analysis_result.get('confidence', 0)
            elif analysis_type in ['has_false_claim', 'false_advertising', 'price_fraud']:
                analysis_result = analysis.get('text_analysis', {})
                if analysis_type == 'has_false_claim':
                    return analysis_result.get('has_false_claim', False)
                elif analysis_type == 'false_advertising':
                    return analysis_result.get('false_advertising', False)
                elif analysis_type == 'price_fraud':
                    return analysis_result.get('price_fraud', False)

        return None

    def _get_suggested_action(self, decision: str, confidence: int) -> str:
        if decision == DecisionType.PENDING.value:
            return "等待更多证据或人工介入"

        if confidence >= 90:
            return f"强烈建议自动执行判定结果: {decision}"
        elif confidence >= 70:
            return f"建议优先考虑判定结果: {decision}，可人工复核"
        elif confidence >= 50:
            return f"判定结果: {decision}，置信度一般，建议人工仲裁"
        else:
            return f"判定结果: {decision}，置信度低，必须人工仲裁"

    def test_rule(self, rule_dict: Dict, test_data: Dict) -> Dict:
        rule = self._dict_to_rule(rule_dict)
        ticket_data = test_data.get('ticket', {})
        evidences = test_data.get('evidences', [])

        result = self._check_condition(rule, ticket_data, evidences)

        return {
            'rule_id': rule.id,
            'rule_name': rule.name,
            'rule_code': rule.code,
            'test_passed': result,
            'test_data': {
                'ticket': ticket_data,
                'evidences': evidences
            }
        }

    def _dict_to_rule(self, rule_dict: Dict) -> Rule:
        return Rule(
            id=rule_dict.get('id', 0),
            name=rule_dict.get('name', ''),
            code=rule_dict.get('code', ''),
            category=rule_dict.get('category', ''),
            description=rule_dict.get('description', ''),
            conditions=rule_dict.get('conditions', '{}'),
            actions=rule_dict.get('actions', '{}'),
            priority=rule_dict.get('priority', 50),
            weight=rule_dict.get('weight', 100),
            is_active=rule_dict.get('is_active', True),
            version=rule_dict.get('version', 1)
        )

    def add_rule(self, rule: Rule) -> None:
        self.rules.append(rule)
        self.rules.sort(key=lambda x: x.priority, reverse=True)
        logger.info(f"Added rule: {rule.code}")

    def remove_rule(self, code: str) -> bool:
        for i, rule in enumerate(self.rules):
            if rule.code == code:
                self.rules.pop(i)
                logger.info(f"Removed rule: {code}")
                return True
        return False

    def get_rules_by_category(self, category: str) -> List[Rule]:
        return [r for r in self.rules if r.category == category and r.is_active]

    def get_all_rules(self) -> List[Dict]:
        return [
            {
                'id': r.id,
                'name': r.name,
                'code': r.code,
                'category': r.category,
                'description': r.description,
                'conditions': json.loads(r.conditions),
                'actions': json.loads(r.actions),
                'priority': r.priority,
                'weight': r.weight,
                'is_active': r.is_active,
                'version': r.version
            }
            for r in self.rules
        ]
