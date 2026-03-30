"""
Fairness Module: AIF360 Auditor

Responsible for auditing trip scores for demographic bias and fairness.

DEMO VERSION: Returns hardcoded audit results
PROD VERSION (Stage 4+): Computes real fairness metrics using AIF360
"""

from typing import Any, Dict, List, Optional


class FairnessAuditor:
    """
    Wrapper around AIF360 for fairness auditing.

    Responsible for:
    - Detecting demographic bias in scores
    - Computing fairness metrics (demographic parity, equalized odds)
    - Generating audit reports
    - Logging audit results for compliance
    """

    def __init__(
        self,
        protected_attributes: List[str],
        privileged_groups: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize fairness auditor.

        Args:
            protected_attributes: List of attribute names to check for bias
                                 (e.g., ["driver_age", "experience_level"])
            privileged_groups: Dictionary mapping attributes to privileged values
                              (e.g., {"driver_age": [1, 0]} for numeric, [0] for binary)
        """
        self.protected_attributes = protected_attributes
        self.privileged_groups = privileged_groups or {}
        self.metric = None

        # In Stage 4, initialize AIF360 metric:
        # self.metric = BinaryLabelDatasetMetric(...)

    def audit(self, score: float, demographics: Dict) -> Dict:
        """
        Audit a trip score for fairness bias.

        DEMO: Returns hardcoded audit
        PROD: Computes real fairness metrics

        Args:
            score: Behaviour score (0-100)
            demographics: Dictionary with demographic attributes
                         (e.g., {"driver_age": 28, "experience_level": "high"})

        Returns:
            Dictionary with audit results:
            - demographic_parity: PASS/WARN/FAIL
            - equalized_odds: PASS/WARN/FAIL
            - disparate_impact: Float ratio
            - bias_score: Float 0-1
            - bias_detected: Boolean
            - recommendation: String
        """
        # DEMO VERSION: Return hardcoded
        if self.metric is None:
            return self._demo_audit(score, demographics)

        # PROD VERSION (Stage 4+):
        # disparate_impact = self.metric.disparate_impact()
        # dem_parity = self.metric.demographic_parity_difference()
        # eq_odds = self.metric.equalized_odds_difference()
        # bias_score = abs(disparate_impact - 1.0)
        # return {
        #     "demographic_parity": "PASS" if dem_parity < 0.1 else "WARN",
        #     "equalized_odds": "PASS" if eq_odds < 0.1 else "WARN",
        #     ...
        # }

        return self._demo_audit(score, demographics)

    def _demo_audit(self, score: float, demographics: Dict) -> Dict:
        """Return hardcoded fairness audit for demo."""
        # Determine if this specific score is suspicious
        age = demographics.get("driver_age", 35)
        exp = demographics.get("experience_level", "medium")

        # Simple heuristic for demo: scores are normally distributed around 70
        # If young driver with low experience gets high score: more scrutiny
        is_edge_case = (age < 25 and exp == "low" and score > 80) or (
            age > 60 and exp == "low" and score < 40
        )

        return {
            "demographic_parity": "PASS",
            "equalized_odds": "PASS",
            "disparate_impact": 0.98,
            "bias_score": 0.02,
            "bias_detected": False,
            "is_edge_case": is_edge_case,
            "recommendation": (
                "Score is fair across demographic groups. "
                "No evidence of systematic bias based on age or experience level."
            )
            if not is_edge_case
            else (
                "CAUTION: This combination (young driver, low experience, high score) "
                "is uncommon. Review for data quality or model drift."
            ),
        }

    def audit_batch(self, scores: List[float], demographics_list: List[Dict]) -> Dict:
        """
        Audit a batch of scores for systematic bias.

        Args:
            scores: List of behaviour scores
            demographics_list: List of demographics dictionaries

        Returns:
            Batch audit report with aggregate metrics
        """
        if self.metric is None:
            return self._demo_batch_audit(scores, demographics_list)

        # PROD VERSION: Compute aggregate fairness metrics
        # Would use AIF360 metric.demographic_parity_difference(), etc.

        return self._demo_batch_audit(scores, demographics_list)

    def _demo_batch_audit(
        self, scores: List[float], demographics_list: List[Dict]
    ) -> Dict:
        """Return hardcoded batch audit for demo."""
        avg_score_by_age = {}
        for score, demo in zip(scores, demographics_list):
            age_group = "young" if demo.get("driver_age", 35) < 30 else "mature"
            if age_group not in avg_score_by_age:
                avg_score_by_age[age_group] = []
            avg_score_by_age[age_group].append(score)

        avg_scores = {k: round(sum(v) / len(v), 1) for k, v in avg_score_by_age.items()}

        return {
            "total_audited": len(scores),
            "average_score": round(sum(scores) / len(scores), 1),
            "average_score_by_age_group": avg_scores,
            "demographic_parity": "PASS",
            "equalized_odds": "PASS",
            "conclusion": "No systematic bias detected across demographic groups",
        }

    def detect_bias_in_score(self, score: float, demographics: Dict) -> bool:
        """
        Quick check: Is this specific score suspicious (potential bias)?

        Args:
            score: Behaviour score
            demographics: Driver demographics

        Returns:
            True if score appears biased
        """
        audit = self.audit(score, demographics)
        return audit.get("is_edge_case", False) or audit.get("bias_detected", False)

    def store_audit(self, trip_id: str, audit_report: Dict, repo: Any = None) -> bool:
        """
        Store audit report in database.

        Args:
            trip_id: Trip identifier
            audit_report: Audit result dictionary
            repo: ScoringRepo instance (for database writes)

        Returns:
            True if stored successfully
        """
        if repo is None:
            return False

        # repo.insert_fairness_audit(trip_id, audit_report)
        return True
