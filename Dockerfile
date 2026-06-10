# Base image with Python 3.11
FROM python:3.11-slim

# Set environment variable to prevent Python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system packages required for OpenCV and Tesseract OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy source directories and settings
COPY backend/ /app/backend/
COPY dataset/ /app/dataset/

# Create logs directory
RUN mkdir -p /app/logs

# Expose default API server port
EXPOSE 8000

# Run FastAPI using uvicorn binding to all interfaces
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
