"""
XAI Module: SHAP Explainer

Responsible for generating explanations of trip scores using SHAP values.

DEMO VERSION: Returns hardcoded explanations
PROD VERSION (Stage 3+): Computes real SHAP values from XGBoost model
"""

from typing import Any, Dict, List, Optional


class SHAPExplainer:
    """
    Wrapper around SHAP TreeExplainer for trip scoring.

    Responsible for:
    - Computing SHAP values for trip score
    - Identifying top contributing features
    - Generating human-readable explanations
    - Storing explanations in database
    """

    def __init__(self, model: Any = None, background_data: Optional[List[Dict]] = None):
        """
        Initialize SHAP explainer.

        Args:
            model: XGBoost model instance (None in demo)
            background_data: Background dataset for SHAP baseline (None in demo)
        """
        self.model = model
        self.background_data = background_data
        self.explainer = None

        # In Stage 3, initialize explainer:
        # self.explainer = shap.TreeExplainer(model, background_data)

    def explain(self, features: Dict, trip_id: str = None) -> Dict:
        """
        Explain trip score using SHAP values.

        DEMO: Returns hardcoded explanation
        PROD: Computes real SHAP values

        Args:
            features: Feature dictionary with keys like jerk_mean, speed_std_dev, etc.
            trip_id: Trip identifier (for database storage)

        Returns:
            Dictionary with:
            - top_features: List of (feature, shap_value) tuples
            - base_score: Expected model output (SHAP base value)
            - final_score: Actual score
            - narrative: Human-readable explanation
        """
        # DEMO VERSION: Return hardcoded
        if self.model is None:
            return self._demo_explanation(features)

        # PROD VERSION (Stage 3+):
        # shap_values = self.explainer.shap_values(features_array)
        # top_features = sorted([(name, val) for name, val in zip(feature_names, shap_values)])
        # narrative = self._generate_narrative(top_features, base_score, final_score)
        # return {
        #     "top_features": top_features,
        #     "base_score": self.explainer.expected_value,
        #     "final_score": score,
        #     "narrative": narrative
        # }

        return self._demo_explanation(features)

    def _demo_explanation(self, features: Dict) -> Dict:
        """Return hardcoded SHAP explanation for demo."""
        return {
            "top_features": [
                {
                    "feature": "jerk_mean",
                    "value": round(features.get("jerk_mean", 0.015), 4),
                    "shap_value": 0.25,
                    "contribution": "positive",
                },
                {
                    "feature": "speed_std_dev",
                    "value": round(features.get("speed_std_dev", 12.0), 2),
                    "shap_value": 0.18,
                    "contribution": "positive",
                },
                {
                    "feature": "mean_lateral_g",
                    "value": round(features.get("mean_lateral_g", 0.03), 3),
                    "shap_value": 0.12,
                    "contribution": "positive",
                },
                {
                    "feature": "idle_ratio",
                    "value": round(features.get("idle_ratio", 0.15), 3),
                    "shap_value": -0.08,
                    "contribution": "negative",
                },
            ],
            "base_score": 50.0,
            "final_score": 74.3,
            "narrative": (
                "The driver's smooth acceleration and braking (low jerk, +0.25) "
                "combined with consistent speed control (+0.18) are the main drivers "
                "of the high score. Smooth cornering (+0.12) also helps. "
                "Excessive idle time (-0.08) slightly reduces the score. "
                "Overall: Good smoothness and control."
            ),
        }

    def explain_text(self, shap_values: Dict) -> str:
        """
        Generate human-readable narrative from SHAP values.

        Args:
            shap_values: Output from explain()

        Returns:
            String narrative suitable for human consumption
        """
        return shap_values.get("narrative", "Unable to generate explanation")

    def store_explanation(
        self, trip_id: str, explanation: Dict, repo: Any = None
    ) -> bool:
        """
        Store explanation in database.

        Args:
            trip_id: Trip identifier
            explanation: SHAP explanation dictionary
            repo: ScoringRepo instance (for database writes)

        Returns:
            True if stored successfully
        """
        if repo is None:
            return False

        # repo.insert_shap_explanation(trip_id, explanation)
        return True
