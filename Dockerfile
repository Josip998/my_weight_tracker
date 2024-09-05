FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the FastAPI app and Kafka consumer script
COPY . .

# Expose the port for FastAPI
EXPOSE 5000

# Start both the FastAPI app and Kafka consumer
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 5000 & python kafka_consumer.py"]
