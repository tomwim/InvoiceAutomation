# Use slim Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (better layer caching)
COPY ./blob_storage_listener/requirements.txt .

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./blob_storage_listener/src ./src

# Copy shared common code (relative to build context!)
COPY ../common ./common

# Expose FastAPI port
EXPOSE 8001

# Run FastAPI with Uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]