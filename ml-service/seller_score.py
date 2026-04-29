import math
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ScoreChangeType(Enum):
    WIN = "win"
    LOSE = "lose"
    TIMEOUT = "timeout"
    COMPLAINT = "complaint"
    PRAISE = "praise"
    SLA_VIOLATION = "sla_violation"
    QUICK_RESOLUTION = "quick_resolution"


@dataclass
class ScoreChange:
    type: str
    amount: float
    reason: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoreCalculationResult:
    current_score: float
    new_score: float
    changes: List[ScoreChange]
    rating: str
    trend: str
    factors: Dict[str, Any]
    recommendations: List[str]


class SellerScoreCalculator:
    def __init__(self):
        self.base_score = 100.0
        self.min_score = 0.0
        self.max_score = 100.0

        self.score_change_rules = {
            'lose': {
                'base_penalty': -3.0,
                'per_1000_amount': -0.5,
                'max_penalty': -10.0
            },
            'win': {
                'base_bonus': 0.5,
                'max_bonus': 2.0
            },
            'timeout': {
                'base_penalty': -2.0,
                'per_hour': -0.5,
                'max_penalty': -8.0
            },
            'sla_violation': {
                'base_penalty': -1.5,
                'per_violation': -0.5,
                'max_penalty': -5.0
            },
            'quick_resolution': {
                'base_bonus': 1.0,
                'max_bonus': 3.0
            },
            'complaint': {
                'base_penalty': -1.0,
                'if_verified': -2.0,
                'max_penalty': -5.0
            },
            'praise': {
                'base_bonus': 0.3,
                'max_bonus': 1.0
            }
        }

        self.rating_thresholds = [
            (90.0, '优秀', 'gold'),
            (80.0, '良好', 'silver'),
            (70.0, '一般', 'bronze'),
            (60.0, '及格', 'standard'),
            (0.0, '较差', 'warning')
        ]

        self.weight_factors = {
            'dispute_resolution': 0.35,
            'response_time': 0.25,
            'resolution_rate': 0.20,
            'customer_satisfaction': 0.15,
            'historical_performance': 0.05
        }

        logger.info("Seller Score Calculator initialized")

    def calculate_score(
        self,
        seller_data: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        base_score = seller_data.get('service_score', self.base_score)

        score_components = self._calculate_components(seller_data, history)

        weighted_score = 0.0
        for component, weight in self.weight_factors.items():
            weighted_score += score_components.get(component, 0.7) * weight

        final_score = (base_score * 0.6 + weighted_score * 100 * 0.4)
        final_score = max(self.min_score, min(self.max_score, final_score))

        rating, rating_level = self._get_rating(final_score)
        trend = self._calculate_trend(seller_data, history)

        factors = {
            'components': score_components,
            'weights': self.weight_factors,
            'base_score': base_score,
            'weighted_score': weighted_score * 100
        }

        recommendations = self._generate_recommendations(final_score, score_components, history)

        return {
            'current_score': round(base_score, 2),
            'new_score': round(final_score, 2),
            'rating': rating,
            'rating_level': rating_level,
            'trend': trend,
            'factors': factors,
            'recommendations': recommendations
        }

    def _calculate_components(
        self,
        seller_data: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        dispute_count = seller_data.get('dispute_count', 0)
        win_count = seller_data.get('dispute_wins', 0)
        lose_count = seller_data.get('dispute_losses', 0)
        avg_resolve_hours = seller_data.get('avg_resolve_hours', 24)

        resolution_rate = 0.5
        if dispute_count > 0:
            resolution_rate = (win_count + (dispute_count - win_count - lose_count) * 0.5) / dispute_count

        if avg_resolve_hours <= 12:
            response_score = 1.0
        elif avg_resolve_hours <= 24:
            response_score = 0.8
        elif avg_resolve_hours <= 48:
            response_score = 0.6
        else:
            response_score = 0.3

        recent_losses = sum(1 for h in history if h.get('change', 0) < 0)
        recent_total = max(len(history), 1)
        customer_satisfaction = 1.0 - (recent_losses / recent_total * 0.5)

        historical_performance = 0.7
        total_changes = len(history)
        if total_changes > 0:
            positive_changes = sum(1 for h in history if h.get('change', 0) > 0)
            historical_performance = positive_changes / total_changes

        return {
            'dispute_resolution': min(1.0, resolution_rate),
            'response_time': response_score,
            'resolution_rate': min(1.0, resolution_rate),
            'customer_satisfaction': max(0.0, customer_satisfaction),
            'historical_performance': max(0.0, min(1.0, historical_performance))
        }

    def update_score(
        self,
        current_score: float,
        decision: str,
        amount: float,
        seller_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        changes = []
        new_score = current_score

        if decision in ['refund', 'return', 'seller_responsible']:
            rule = self.score_change_rules['lose']
            base_penalty = rule['base_penalty']
            amount_penalty = (amount // 1000) * rule['per_1000_amount']
            total_penalty = max(rule['max_penalty'], base_penalty + amount_penalty)

            new_score += total_penalty
            changes.append(ScoreChange(
                type='lose',
                amount=total_penalty,
                reason='仲裁败诉/支持买家诉求',
                details={'decision': decision, 'amount': amount}
            ))

        elif decision in ['reject', 'buyer_responsible']:
            rule = self.score_change_rules['win']
            bonus = min(rule['max_bonus'], rule['base_bonus'])
            new_score += bonus
            changes.append(ScoreChange(
                type='win',
                amount=bonus,
                reason='仲裁胜诉/驳回买家诉求',
                details={'decision': decision}
            ))

        elif decision == 'partial_refund':
            rule = self.score_change_rules['lose']
            partial_penalty = rule['base_penalty'] * 0.5
            new_score += partial_penalty
            changes.append(ScoreChange(
                type='lose',
                amount=partial_penalty,
                reason='部分支持买家诉求',
                details={'decision': 'partial_refund', 'amount': amount}
            ))

        avg_resolve_hours = seller_stats.get('avg_resolve_hours', 24)
        if avg_resolve_hours <= 12:
            rule = self.score_change_rules['quick_resolution']
            bonus = min(rule['max_bonus'], rule['base_bonus'])
            new_score += bonus
            changes.append(ScoreChange(
                type='quick_resolution',
                amount=bonus,
                reason='快速响应奖励',
                details={'resolve_hours': avg_resolve_hours}
            ))

        new_score = max(self.min_score, min(self.max_score, new_score))

        rating, rating_level = self._get_rating(new_score)
        trend = self._determine_trend(current_score, new_score)

        return {
            'current_score': round(current_score, 2),
            'new_score': round(new_score, 2),
            'change': round(new_score - current_score, 2),
            'rating': rating,
            'rating_level': rating_level,
            'trend': trend,
            'changes': [
                {
                    'type': c.type,
                    'amount': c.amount,
                    'reason': c.reason,
                    'details': c.details
                }
                for c in changes
            ]
        }

    def predict_impact(
        self,
        seller_data: Dict[str, Any],
        ticket_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        current_score = seller_data.get('service_score', self.base_score)
        dispute_count = seller_data.get('dispute_count', 0)
        avg_resolve_hours = seller_data.get('avg_resolve_hours', 24)

        ticket_type = ticket_data.get('type', 'refund')
        ticket_amount = ticket_data.get('request_amount', 0)
        ticket_category = ticket_data.get('category', '')

        win_probability = self._calculate_win_probability(
            seller_data, ticket_data
        )

        scenarios = []

        win_scenario = self.update_score(
            current_score, 'reject', 0,
            {'avg_resolve_hours': avg_resolve_hours}
        )
        scenarios.append({
            'scenario': 'win',
            'probability': win_probability,
            'expected_score': win_scenario['new_score'],
            'expected_change': win_scenario['change'],
            'description': '仲裁胜诉，驳回买家诉求'
        })

        lose_amount = ticket_amount
        lose_scenario = self.update_score(
            current_score, 'refund', lose_amount,
            {'avg_resolve_hours': avg_resolve_hours}
        )
        scenarios.append({
            'scenario': 'lose',
            'probability': 1 - win_probability,
            'expected_score': lose_scenario['new_score'],
            'expected_change': lose_scenario['change'],
            'description': '仲裁败诉，支持买家诉求'
        })

        expected_score = (
            win_scenario['new_score'] * win_probability +
            lose_scenario['new_score'] * (1 - win_probability)
        )

        risk_assessment = self._assess_risk(
            current_score, lose_scenario['new_score'], win_probability
        )

        return {
            'current_score': round(current_score, 2),
            'expected_score': round(expected_score, 2),
            'win_probability': round(win_probability * 100, 1),
            'scenarios': scenarios,
            'risk_assessment': risk_assessment,
            'recommendations': self._generate_risk_recommendations(
                win_probability, current_score, ticket_category
            )
        }

    def _calculate_win_probability(
        self,
        seller_data: Dict[str, Any],
        ticket_data: Dict[str, Any]
    ) -> float:
        base_probability = 0.5

        seller_score = seller_data.get('service_score', 80)
        if seller_score >= 90:
            base_probability += 0.15
        elif seller_score >= 80:
            base_probability += 0.1
        elif seller_score >= 70:
            base_probability += 0.05
        elif seller_score < 60:
            base_probability -= 0.1

        dispute_count = seller_data.get('dispute_count', 0)
        win_rate = 0.5
        if dispute_count > 0:
            win_rate = seller_data.get('dispute_wins', 0) / dispute_count
            base_probability += (win_rate - 0.5) * 0.2

        ticket_category = ticket_data.get('category', '')
        high_risk_categories = ['quality', 'advertising', 'logistics']
        if ticket_category in high_risk_categories:
            base_probability -= 0.1

        auto_decision = ticket_data.get('auto_decision')
        if auto_decision:
            if auto_decision in ['refund', 'return', 'seller_responsible']:
                base_probability -= 0.15
            elif auto_decision in ['reject', 'buyer_responsible']:
                base_probability += 0.15

        return max(0.05, min(0.95, base_probability))

    def _assess_risk(
        self,
        current_score: float,
        worst_case_score: float,
        win_probability: float
    ) -> Dict[str, Any]:
        score_drop = current_score - worst_case_score

        risk_level = 'low'
        if score_drop >= 5.0:
            risk_level = 'high'
        elif score_drop >= 3.0:
            risk_level = 'medium'

        current_rating, _ = self._get_rating(current_score)
        worst_rating, _ = self._get_rating(worst_case_score)

        rating_drop = current_rating != worst_rating

        return {
            'risk_level': risk_level,
            'score_drop': round(score_drop, 2),
            'worst_case_score': round(worst_case_score, 2),
            'current_rating': current_rating,
            'worst_case_rating': worst_rating,
            'rating_drop_risk': rating_drop,
            'win_probability': round(win_probability * 100, 1)
        }

    def _get_rating(self, score: float) -> tuple:
        for threshold, rating, level in self.rating_thresholds:
            if score >= threshold:
                return rating, level
        return '较差', 'warning'

    def _calculate_trend(
        self,
        seller_data: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> str:
        if not history:
            return 'stable'

        recent_changes = history[-5:] if len(history) >= 5 else history
        total_change = sum(h.get('change', 0) for h in recent_changes)

        if total_change > 2.0:
            return 'rising'
        elif total_change < -2.0:
            return 'falling'
        else:
            return 'stable'

    def _determine_trend(self, old_score: float, new_score: float) -> str:
        diff = new_score - old_score
        if diff > 1.0:
            return 'rising'
        elif diff < -1.0:
            return 'falling'
        else:
            return 'stable'

    def _generate_recommendations(
        self,
        score: float,
        components: Dict[str, float],
        history: List[Dict[str, Any]]
    ) -> List[str]:
        recommendations = []

        if score >= 90:
            recommendations.append('您的服务评分优秀，建议继续保持')
        elif score >= 80:
            recommendations.append('您的服务评分良好，建议进一步提升')
        elif score >= 70:
            recommendations.append('您的服务评分一般，建议关注客户满意度')
        elif score >= 60:
            recommendations.append('您的服务评分偏低，建议及时改进服务质量')
        else:
            recommendations.append('您的服务评分较差，存在被处罚风险，建议立即改进')

        response_time = components.get('response_time', 0.5)
        if response_time < 0.6:
            recommendations.append('响应时间偏慢，建议加快处理速度')

        resolution_rate = components.get('resolution_rate', 0.5)
        if resolution_rate < 0.6:
            recommendations.append('纠纷解决率偏低，建议提升服务质量')

        customer_satisfaction = components.get('customer_satisfaction', 0.5)
        if customer_satisfaction < 0.6:
            recommendations.append('客户满意度偏低，建议加强沟通和服务')

        recent_losses = sum(1 for h in history[-5:] if h.get('change', 0) < 0) if history else 0
        if recent_losses >= 2:
            recommendations.append('近期败诉较多，建议分析原因并改进')

        if not recommendations:
            recommendations.append('各项指标表现良好，继续保持')

        return recommendations

    def _generate_risk_recommendations(
        self,
        win_probability: float,
        current_score: float,
        ticket_category: str
    ) -> List[str]:
        recommendations = []

        if win_probability < 0.3:
            recommendations.append('胜诉概率较低，建议主动协商解决')
            recommendations.append('考虑主动提供补偿方案以减少损失')
        elif win_probability < 0.5:
            recommendations.append('胜诉概率一般，建议准备充分证据')
        elif win_probability < 0.7:
            recommendations.append('胜诉概率较高，建议保持现有策略')
        else:
            recommendations.append('胜诉概率很高，建议按正常流程处理')

        if current_score < 70:
            recommendations.append('当前服务评分偏低，败诉风险影响较大')
            recommendations.append('建议优先考虑协商解决，避免进一步扣分')

        high_risk_categories = ['quality', 'advertising']
        if ticket_category in high_risk_categories:
            recommendations.append(f'当前纠纷类型({ticket_category})风险较高')
            recommendations.append('建议重点准备相关证据材料')

        return recommendations

    def get_score_change_rules(self) -> Dict[str, Any]:
        return self.score_change_rules

    def get_rating_thresholds(self) -> List[Dict[str, Any]]:
        return [
            {'min_score': threshold, 'rating': rating, 'level': level}
            for threshold, rating, level in self.rating_thresholds
        ]
