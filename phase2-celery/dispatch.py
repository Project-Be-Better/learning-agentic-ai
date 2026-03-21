from tasks import app, safety_task, scoring_task, sentiment_task


if __name__ == "__main__":
    trip_id = "trip_001"
    print(f"Dispatching all agents for {trip_id}...\n")

    safety_result = safety_task.delay(trip_id)
    scoring_result = scoring_task.delay(trip_id)
    sentiment_result = sentiment_task.delay(trip_id)

    print(f"Safety   task id → {safety_result.id}")
    print(f"Scoring  task id → {scoring_result.id}")
    print(f"Sentiment task id → {sentiment_result.id}")

    print("\n Waiting for all results...\n")

    safety_output = safety_result.get(timeout=5)
    print(f"Safety   → {safety_output}")
    scoring_output = scoring_result.get(timeout=10)
    print(f"Scoring  → {scoring_output}")
    sentiment_output = sentiment_result.get(timeout=15)
    print(f"Sentiment → {sentiment_output}")

    print("\n[Done]")
