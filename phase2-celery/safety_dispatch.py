from tasks import app, safety_task, Priority, Queue

if __name__ == "__main__":
    trip_id = "trip_001"
    print(f"Dispatching tasks at different priorities{trip_id}...\n")

    # dispatch four tasks to the SAME queue at different priorities
    # stop the worker first, dispatch all four, then start worker
    # so they all queue up and priority ordering is visible

    low_result = safety_task.apply_async(
        (trip_id,), queue=Queue.SAFETY, priority=Priority.LOW
    )
    medium_result = safety_task.apply_async(
        (trip_id,), queue=Queue.SAFETY, priority=Priority.MEDIUM
    )
    high_result = safety_task.apply_async(
        (trip_id,), queue=Queue.SAFETY, priority=Priority.HIGH
    )
    critical_result = safety_task.apply_async(
        (trip_id,), queue=Queue.SAFETY, priority=Priority.CRITICAL
    )

    print(f"LOW      task id → {low_result.id}")
    print(f"MEDIUM      task id → {medium_result.id}")
    print(f"HIGH      task id → {high_result.id}")
    print(f"CRITICAL      task id → {critical_result.id}")

    low_output = low_result.get(timeout=15)
    medium_output = medium_result.get(timeout=15)
    high_output = high_result.get(timeout=15)
    critical_output = critical_result.get(timeout=15)

    print(f"LOW      → {low_output}")
    print(f"MEDIUM      → {medium_output}")
    print(f"HIGH      → {high_output}")
    print(f"CRITICAL      → {critical_output}")

    print("\n[Done]")
