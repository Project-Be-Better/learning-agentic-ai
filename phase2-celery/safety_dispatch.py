from tasks import app, safety_task, Priority, Queue  # 📋

if __name__ == "__main__":  # ✋
    trip_id = "trip_001"

    # ✋ dispatch ALL four before collecting any results
    # this is what creates queue competition
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

    # 📋
    print(f"LOW      → {low_result.id}")
    print(f"MEDIUM   → {medium_result.id}")
    print(f"HIGH     → {high_result.id}")
    print(f"CRITICAL → {critical_result.id}")
    print("\nAll queued — now watch worker terminal for processing order\n")

    # ✋ collect after all four are queued
    # each task takes 2 seconds — four tasks = 8 seconds total
    low_output = low_result.get(timeout=30)
    medium_output = medium_result.get(timeout=30)
    high_output = high_result.get(timeout=30)
    critical_output = critical_result.get(timeout=30)

    # 📋
    print(f"LOW      → {low_output}")
    print(f"MEDIUM   → {medium_output}")
    print(f"HIGH     → {high_output}")
    print(f"CRITICAL → {critical_output}")
    print("\n[Done]")
