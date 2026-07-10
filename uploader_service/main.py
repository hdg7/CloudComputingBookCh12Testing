from fastapi import FastAPI, UploadFile, File, HTTPException
import aio_pika
import asyncio

from typing import List

import ast
import aioredis

import os


app = FastAPI()
RABBITMQ_URL = "amqp://guest:guest@rabbitmq/"

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CHANNEL_NAME = "database"

async def connect_rabbitmq():
    while True:
        try:
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            channel = await connection.channel()
            await channel.declare_queue("image_tasks", durable=True)
            app.state.connection = connection
            app.state.channel = channel
            print("Connected to RabbitMQ")
            break
        except Exception as e:
            print("Waiting for RabbitMQ...")
            await asyncio.sleep(2)

            
@app.on_event("startup")
async def startup():
    await connect_rabbitmq()
    app.state.redis = await aioredis.from_url(REDIS_URL)

@app.on_event("shutdown")
async def shutdown():
    await app.state.connection.close()       
    await app.state.redis.close()

@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    image_bytes = await file.read()
    message = aio_pika.Message(body=image_bytes)
    await app.state.channel.default_exchange.publish(message, routing_key="image_tasks")
    return {"status": "queued"}


@app.get("/detections/")
async def get_detections_api() -> List[dict]:
    detections = await app.state.redis.get("current_detections")
    if detections:

        decoded = detections.decode("utf-8")

        tuples_list = ast.literal_eval(decoded) 

        result = []
        for item in tuples_list:
            result.append({
                "id": item[0],
                "label": item[1],
                "score": item[2],
                "x1": item[3],
                "y1": item[4],
                "x2": item[5],
                "y2": item[6],
                "image_path": item[7]
            })
        return result
    return []
                                                                                    
@app.put("/detections/{id}/")
async def update_detection(id: int, label: str):
    detections = await app.state.redis.get("current_detections")
    if not detections:
        raise HTTPException(status_code=404, detail="No detections found")

    decoded = detections.decode("utf-8")
    tuples_list = ast.literal_eval(decoded)

    updated = False
    new_tuples_list = []
    for item in tuples_list:
        if item[0] == id:
            new_item = (item[0], label, item[2], item[3], item[4], item[5], item[6], item[7])
            new_tuples_list.append(new_item)
            updated = True
        else:
            new_tuples_list.append(item)

    if not updated:
        raise HTTPException(status_code=404, detail="Detection ID not found")

    await app.state.redis.set("current_detections", str(new_tuples_list))
    return {"status": "updated"}

@app.delete("/detections/{id}/")
async def delete_detection(id: int):
    detections = await app.state.redis.get("current_detections")
    if not detections:
        raise HTTPException(status_code=404, detail="No detections found")

    decoded = detections.decode("utf-8")
    tuples_list = ast.literal_eval(decoded)

    new_tuples_list = [item for item in tuples_list if item[0] != id]

    if len(new_tuples_list) == len(tuples_list):
        raise HTTPException(status_code=404, detail="Detection ID not found")

    await app.state.redis.set("current_detections", str(new_tuples_list))
    return {"status": "deleted"}


@app.get("/health")
async def health():
    return {"status": "ok"}
