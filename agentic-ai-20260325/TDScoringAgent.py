from typing import Any, Dict

from TDAgentBase import TDAgentBase


class TDScoringAgent(TDAgentBase):
    """
    Scoring Agent: Scores a trip based on smoothness.

    This is what a subclass looks like. Override _execute_logic() only.
    Intent Gate protection is inherited automatically.
    """

    def _execute_logic(self, trip_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pure logic. Never sees the capsule
        """
        trip_pings = trip_context.get("trip_pings", [])
        harsh_events = trip_context.get("harsh_events", 0)

        # Simple rule-based scoring
        base_score = 100
        score = max(0, base_score - (harsh_events) * 5)

        return {
            "trip_score": score,
            "pings_count": len(trip_pings),
            "harsh_events_count": harsh_events,
        }
