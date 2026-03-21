import json
import threading
import time

from typing import Final
from redis_client import RedisClient
from keys import RedisSchema

TRIP_ID: Final[str] = "trip_001"


def orchestrator_listener(r_client: RedisClient, channel: str) -> None:
    """
    Subscribes to a trip channel and reacts to agent completion events
    """

    pubsub = r_client.client.pubsub()
    pubsub.subscribe(channel)

    print(f"[Orchestrator] Listening on → {channel}\n", flush=True)

    for message in pubsub.listen():
        if message["type"] != "message":
            continue

        event: dict = json.loads(message["data"])
        agent: str = event["agent"]
        status: str = event["status"]

        print(f"[Orchestrator] ← {agent} reported: {status}", flush=True)

        # react based on which agent completed
        match agent:
            case "safety":
                print("[Orchestrator] Safety done → can dispatch Scoring\n")
            case "scoring":
                print("[Orchestrator] Scoring done → can dispatch Coaching\n")
            case "sentiment":
                print("[Orchestrator] Sentiment done → all agents complete\n")

        if event.get("final"):
            print("[Orchestrator] Final event received → closing listener")
            pubsub.unsubscribe()
            break


def safety_agent_task(r_client: RedisClient, channel: str) -> None:
    """
    Simulates the Safety Agent: analyzes context and publishes a result.
    """

    print("[Safety Agent]   → starting task...", flush=True)
    time.sleep(2)

    event: dict = {
        "agent": "safety",
        "trip_id": TRIP_ID,
        "status": "done",
        "score": 0.82,
        "final": False,
    }

    event_json = json.dumps(event)
    r_client.client.publish(channel, event_json)

    events_key = RedisSchema.Trip.events_channel(TRIP_ID)
    r_client.client.lpush(events_key, json.dumps(event))
    r_client.client.expire(events_key, 120)

    print("[Safety Agent]   → event published", flush=True)
    time.sleep(0.1)


def scoring_agent_task(r_client: RedisClient, channel: str) -> None:
    """
    Simulates the Scoring Agent: analyzes context and publishes a result
    """

    print("[Scoring Agent]  → starting task...", flush=True)
    time.sleep(3)

    event: dict = {
        "agent": "scoring",
        "trip_id": TRIP_ID,
        "status": "done",
        "score": 0.76,
        "final": False,
    }

    event_json = json.dumps(event)
    r_client.client.publish(channel, event_json)

    events_key = RedisSchema.Trip.events_channel(TRIP_ID)
    r_client.client.lpush(events_key, json.dumps(event))
    r_client.client.expire(events_key, 120)

    print("[Scoring Agent]  → event published", flush=True)
    time.sleep(0.1)


def sentiment_agent_task(r_client: RedisClient, channel: str) -> None:
    """
    Simulates the Sentiment Agent: analyzes context and publishes a result.
    """
    print("[Sentiment Agent] → starting task...", flush=True)
    time.sleep(4)

    event: dict = {
        "agent": "sentiment",
        "trip_id": TRIP_ID,
        "status": "done",
        "final": True,
    }
    event_json = json.dumps(event)
    r_client.client.publish(channel, event_json)

    events_key = RedisSchema.Trip.events_channel(TRIP_ID)
    r_client.client.lpush(events_key, json.dumps(event))
    r_client.client.expire(events_key, 120)

    print("[Sentiment Agent] → event published", flush=True)
    time.sleep(0.1)


def main():
    """
    Main entry point to start the simulation.
    """

    channel: str = RedisSchema.Trip.events_channel(TRIP_ID)

    # each client gets its own connection
    # publisher and subscriber MUST use separate connections
    orchestrator_client = RedisClient()
    safety_client = RedisClient()
    scoring_client = RedisClient()
    sentiment_client = RedisClient()

    # start orchestrator in background first
    # daemon=True means it dies automatically when main program exits
    orchestrator_listener_thread = threading.Thread(
        target=orchestrator_listener, args=(orchestrator_client, channel)
    )
    orchestrator_listener_thread.daemon = True
    orchestrator_listener_thread.start()
    time.sleep(2)

    safety_thread = threading.Thread(
        target=safety_agent_task, args=(safety_client, channel)
    )
    scoring_thread = threading.Thread(
        target=scoring_agent_task, args=(scoring_client, channel)
    )
    sentiment_thread = threading.Thread(
        target=sentiment_agent_task, args=(sentiment_client, channel)
    )

    safety_thread.start()
    scoring_thread.start()
    sentiment_thread.start()

    safety_thread.join()
    scoring_thread.join()
    sentiment_thread.join()

    time.sleep(2)
    print("\n[Done] Phase 1 complete.", flush=True)


if __name__ == "__main__":
    main()
