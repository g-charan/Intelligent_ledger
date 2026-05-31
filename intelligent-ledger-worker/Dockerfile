FROM python:3.10-slim

WORKDIR /app

# Copy the requirements file explicitly to tap into Docker build layer caching optimizations
COPY requirements.txt .

# Install production dependencies directly into the system layer inside the container isolation bubble
RUN pip install --no-cache-dir -r requirements.txt

# Copy the runtime worker code execution artifact
COPY worker.py .

# Forces Python to output print statements directly to the Docker logs without internal buffering
CMD ["python", "-u", "worker.py"]