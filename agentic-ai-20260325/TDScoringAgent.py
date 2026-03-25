from typing import Any, Dict
import logging

from TDAgentBase import TDAgentBase

logger = logging.getLogger(__name__)


class TDScoringAgent(TDAgentBase):
    """
    Scoring Agent: Scores a trip based on smoothness.

    This is what a subclass looks like. Override _execute_logic() only.
    Intent Gate protection is inherited automatically.
    """

    def _execute_logic(self, trip_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pure logic. Never sees the capsule.

        Scoring formula:
        - Base score: 100
        - Deduction: 5 points per harsh event
        - Minimum: 0
        """
        trip_pings = trip_context.get("trip_pings", [])
        harsh_events = trip_context.get("harsh_events", 0)

        logger.debug(
            f"Scoring trip with {len(trip_pings)} pings and {harsh_events} harsh events"
        )

        # Simple rule-based scoring
        base_score = 100
        score = max(0, base_score - (harsh_events) * 5)

        logger.debug(f"Calculated trip score: {score}")

        return {
            "trip_score": score,
            "pings_count": len(trip_pings),
            "harsh_events_count": harsh_events,
        }
