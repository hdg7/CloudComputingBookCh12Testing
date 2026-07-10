import asyncio
import aioredis
import json
from db import create_detection, update_detection, delete_detection, read_detections
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CHANNEL_NAME = "database"

async def handle_message(message):
    data = json.loads(message)
    action = data.get("action")
        
    if action == "create_detection":
        detection_data = data["data"]
        create_detection(**detection_data)
        print(f"Created detection: {detection_data}")
        # Update the list of current detections in redis
        detections = read_detections()
        redis = await aioredis.from_url(REDIS_URL)
        await redis.set("current_detections", str(detections))
        
    elif action == "update_detection":
        detection_id = data["data"]["id"]
        update_data = data["data"].copy()
        update_data.pop("id", None) # I remove the id to avoid passing it twice
        update_detection(detection_id, **update_data)
        print(f"Updated detection {detection_id}")
        detections = read_detections()
        redis = await aioredis.from_url(REDIS_URL)
        await redis.set("current_detections", str(detections))

    elif action == "delete_detection":
        detection_id = data["data"]["id"]
        delete_detection(detection_id)
        print(f"Deleted detection {detection_id}")
        detections = read_detections()
        redis = await aioredis.from_url(REDIS_URL)
        await redis.set("current_detections", str(detections))

async def main():
    redis = await aioredis.from_url(REDIS_URL)
    pubsub = redis.pubsub()
    await pubsub.subscribe(CHANNEL_NAME)

    print(f"Subscribed to {CHANNEL_NAME}")
    async for message in pubsub.listen():
        if message["type"] == "message":
            await handle_message(message["data"].decode())

if __name__ == "__main__":
    asyncio.run(main())
