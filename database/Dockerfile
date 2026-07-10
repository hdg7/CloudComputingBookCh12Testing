FROM python:3.10-slim
WORKDIR /app
RUN mkdir /app/data
COPY . .
RUN apt-get update && apt-get install -y libgl1
RUN pip install pillow sqlalchemy aioredis requests==2.31.0
CMD ["python", "dbRedis.py"]
    