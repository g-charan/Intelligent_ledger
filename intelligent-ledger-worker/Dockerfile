FROM python:3.10-slim

WORKDIR /app

# Copy the requirements file explicitly to tap into Docker build layer caching optimizations
COPY requirements.txt .

# Install production dependencies directly into the system layer inside the container isolation bubble
RUN pip install --no-cache-dir -r requirements.txt

# Copy your live script AND your new high-power trained ML model binary into the container image
COPY worker.py .
COPY model.joblib .

# Forces Python to output print logs direct to your stdout console terminal without buffering
CMD ["python", "-u", "worker.py"]