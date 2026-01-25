# Dockerfile (Railway)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (optional, usually not needed for pure FastAPI)
# RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install python deps first (better layer caching)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -U pip \
 && pip install --no-cache-dir -r /app/requirements.txt

# Copy app code + start.sh
COPY . /app

# Ensure start.sh is executable
RUN chmod +x /app/start.sh

# Railway sets PORT автоматически. start.sh обязан использовать $PORT.
CMD ["/app/start.sh"]