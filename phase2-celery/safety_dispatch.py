from tasks import app, safety_task, CRITICAL, HIGH, MEDIUM, LOW

if __name__ == "__main__":
    trip_id = "trip_001"
    print(f"Dispatching tasks at different priorities{trip_id}...\n")

    # dispatch four tasks to the SAME queue at different priorities
    # stop the worker first, dispatch all four, then start worker
    # so they all queue up and priority ordering is visible

    low_result = safety_task.apply_async((trip_id,), queue="safety_queue", priority=LOW)

    print(f"LOW      task id → {low_result.id}")

    low_output = low_result.get(timeout=15)
    print(f"LOW      → {low_output}")

    print("\n[Done]")
