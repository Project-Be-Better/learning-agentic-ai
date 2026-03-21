from tasks import app, analyse_trip

if __name__ == "__main__":
    print("Dispatching task...")

    # .delay() sends the task to the queue and returns immediately
    # it does NOT wait for the result
    result = analyse_trip.delay("trip_001", "safety")

    print(f"Task dispatched — id: {result.id}")
    print("Waiting for result...")

    # .get() blocks here until the worker finishes and returns the result
    output = result.get(timeout=10)

    print(f"Result → {output}")
