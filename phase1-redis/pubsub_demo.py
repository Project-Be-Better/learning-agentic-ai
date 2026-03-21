import json
import threading
import time

from typing import Final
from redis_client import RedisClient
from keys import RedisSchema


TRIP_ID: Final[str] = "trip_001"



def orchestrator_listener(r_client: RedisClient, channel:str)-> None:
    """
    Subscribes to a trip channel and reacts to agent completion events
    """

    pubsub = r_client.client.pubsub()
    pubsub.subscribe(channel)

    print(f"[Orchestrator] Listening on → {channel}\n")

    for message in pubsub.listen():
        if message["type"] != "message":
            continue

        event: dict = json.loads(message["data"])
        agent: str = event["agent"]
        status: str = event["status"]

        print(f"[Orchestrator] ← {agent} reported: {status}")  


    

def safety_agent_task(r_client: RedisClient, channel:str)-> None:
    """
    Simulates the Safety Agent: analyzes context and publishes a result.
    """

    print("[Safety Agent]   → starting task...")
    time.sleep(2)  

    event: dict = {
        "agent": "safety",
        "trip_id": TRIP_ID,
        "status":"done",
        "score": 0.82,
        "final": False,
    }

    r_client.client.publish(channel, json.dumps(event))
    print("[Safety Agent]   → event published") 


def scoring_agent_task(r_client: RedisClient, channel:str)-> None:
    """
    Simulates the Scoring Agent: analyzes context and publishes a result
    """

    print("[Scoring Agent]  → starting task...")
    time.sleep(3)

    event: dict = {
        "agent": "scoring",
        "trip_id": TRIP_ID,
        "status":"done",
        "score": 0.76,
        "final": False,
    }

    r_client.client.publish(channel, json.dumps(event))
    print("[Scoring Agent]  → event published")


def sentiment_agent_task(r_client: RedisClient, channel:str)-> None:
    """
    Simulates the Sentiment Agent: analyzes context and publishes a result.
    """

    event: dict = {
        "agent": "sentiment",
        "trip_id": TRIP_ID,
        "status":"done",
        "final": True,
    }

    r_client.client.publish(channel, json.dumps(event))

    print("[Sentiment Agent] → event published") 




def main():
    """
    Main entry point to start the simulation.
    """

    channel: str = RedisSchema.Trip.events_channel(TRIP_ID)

    # each client gets its own connection 
    # publisher and subscriber MUST use separate connections 

    safety_client = RedisClient()
    scoring_client = RedisClient()
    sentiment_client = RedisClient()

    safety_thread = threading.Thread(target=safety_agent_task, args=(safety_client, channel))
    scoring_thread = threading.Thread(target=scoring_agent_task, args=(scoring_client, channel))
    sentiment_thread = threading.Thread(target=sentiment_agent_task, args=(sentiment_client, channel))

    safety_thread.start()
    scoring_thread.start()
    sentiment_thread.start()

    safety_thread.join()
    scoring_thread.join()
    sentiment_thread.join()

    main()

if __name__ == "__main__":
    main()
