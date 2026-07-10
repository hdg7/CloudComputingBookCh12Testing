import aio_pika, asyncio, io, uuid, os
from ultralytics import YOLO
from PIL import Image, ImageDraw
import aioredis
import json

import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CHANNEL_NAME = "database"

RABBITMQ_URL = "amqp://guest:guest@rabbitmq/"
IMAGE_OUTPUT_DIR = "data/images"
os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)

model = YOLO("yolov8n.pt")


async def create_detection_api(detection_data):
    redis = await aioredis.from_url(REDIS_URL)
    label = detection_data["label"]
    confidence = detection_data["confidence"]
    x1 = detection_data["x1"]
    y1 = detection_data["y1"]
    x2 = detection_data["x2"]
    y2 = detection_data["y2"]
    image_path = detection_data["image_path"]
    message = {
        "action": "create_detection",
        "data": {
            "label": label,
            "confidence": confidence,
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "image_path": image_path
        }
    }
    await redis.publish(CHANNEL_NAME, json.dumps(message))
    return {"status": "queued"}

async def handle_image(message: aio_pika.IncomingMessage):
    async with message.process():
        image = Image.open(io.BytesIO(message.body)).convert("RGB")
        results = model(image)
        detections_ids = []
        # Save annotated image
        filename = f"{uuid.uuid4()}.jpg"
        
        for result in results:
            draw = ImageDraw.Draw(image)
            for box in result.boxes:
                label = model.names[int(box.cls[0])]
                conf = float(box.conf[0])
                x1, y1, x2, y2 = [float(coord.item()) for coord in box.xyxy[0]]
                draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
                draw.text((x1, y1), f"{label} {conf:.2f}", fill="red")

                detection_data = {
                    "label": label,
                    "confidence": conf,
                    "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                    "image_path": IMAGE_OUTPUT_DIR+filename
                }
                await create_detection_api(detection_data)
                
        image_path = os.path.join(IMAGE_OUTPUT_DIR, filename)
        image.save(image_path)
        
        print(f"Processed and saved: {image_path}")
        
async def main():
    while True:
        try:
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            print("Connected to RabbitMQ")
            break
        except Exception as e:
            print("Waiting for RabbitMQ...")
            await asyncio.sleep(2)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1)
    queue = await channel.declare_queue("image_tasks", durable=True)
    await queue.consume(handle_image)
    print("YOLO Worker listening for images...")
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
                                                                                                                                                                                                                                                                                            
