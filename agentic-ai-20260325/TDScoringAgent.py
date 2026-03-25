from typing import Any, Dict

from TDAgentBase import TDAgentBase


class TDScoringAgent(TDAgentBase):
    """
    Inherited from TDAgentBase
    """

    def _execute_logic(self, trip_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pure logic. Never sees the capsule
        """
        trip_pings = trip_context.get("trip_pings", [])
        score = max(0, 100 - (len(trip_pings) * 2))  # Dummy logic
        return {"trip_score": score}

        # trip_id = sanitized_data.get("trip_id", "UNKNOWN")
        # distance_km = sanitized_data.get("distance_km", 0)
        # num_harsh_events = sanitized_data.get("harsh_events", 0)

        # Simple rule: score = 100 - (harsh_events * 5)
        # score = max(0, 100 - (num_harsh_events * 5))

        # result = {
        #     "trip_id": f"ABCD-0000-0000-0000-{trip_id}",
        #     "trip_score": score,
        #     "harsh_events": num_harsh_events,
        #     "distance_km": distance_km,
        # }
        # return result
