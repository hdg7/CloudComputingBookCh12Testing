# Chapter 12 Testing

This repository contains the Testing tutorial mentioned in **Chapter 12** of the book:

[**Cloud Computing for Artificial Intelligence: Concepts, Methods, and Practical Tools**](https://amzn.eu/d/02lMPIKf)

# Distributed Image Processing with FastAPI, YOLO, RabbitMQ, Redis, and SQLite

This repository implements a distributed image processing pipeline using Docker Compose. It integrates multiple services to handle image uploads, object detection, and result management.

## Overview
The system consists of:
- **FastAPI Uploader Service**: Accepts image uploads and queues them via RabbitMQ.
- **YOLO Worker**: Consumes images from RabbitMQ, performs object detection using YOLOv8, annotates images, and updates detection results.
- **Redis**: Provides fast, in-memory storage for detection results.
- **SQLite Database**: Ensures persistent storage of detections.
- **RabbitMQ**: Acts as a message broker for asynchronous communication.
- **Docker Compose**: Orchestrates all services in isolated containers.

## Getting Started

### 1. Build and Start the Services
```bash
sudo docker compose build
sudo docker compose up
```

### 2. Upload an Image
Use `curl` or Postman to send a POST request:
```bash
curl -X POST "http://localhost:8010/upload/" -F "file=@test.jpg"
```

## Services Overview

### RabbitMQ
- Provides message queuing for asynchronous communication.
- Management UI: `http://localhost:15672` (user: guest, pass: guest).

### Uploader Service (FastAPI)
- Endpoints:
  - `POST /upload/`: Upload image and queue for processing.
  - `GET /detections/`: Retrieve detection results.
  - `PUT /detections/{id}/`: Update detection label.
  - `DELETE /detections/{id}/`: Delete detection.

### YOLO Worker
- Listens to `image_tasks` queue.
- Performs object detection using YOLOv8.
- Annotates and saves images to `data/images/`.
- Publishes detection metadata to Redis and SQLite.

### Redis
- Stores latest detection results for fast retrieval.

### SQLite Database
- Provides persistent storage for detections beyond Redis.

## Docker Compose Commands

### Build and Run
```bash
sudo docker compose build
sudo docker compose up
```

### Detached Mode
```bash
sudo docker compose up -d
```

### Stop and Remove Containers
```bash
sudo docker compose down
```

### View Logs
```bash
sudo docker compose logs
```

### Execute Commands Inside Containers
```bash
sudo docker compose exec uploader bash
sudo docker compose exec worker bash
```

### Clean Up
```bash
sudo docker system prune
```

### Testing
To test each service employ the equivalent commands for each service with the docker-compose.test.yml file:
```bash
sudo docker compose -f docker-compose.yml -f docker-compose.test.yml up --build uploader-tests
sudo docker compose -f docker-compose.yml -f docker-compose.test.yml up --build worker-tests
sudo docker compose -f docker-compose.yml -f docker-compose.test.yml up --build database-tests
sudo docker compose -f docker-compose.yml -f docker-compose.test.yml up --build system-tests
```
