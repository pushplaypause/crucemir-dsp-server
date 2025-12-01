FROM python:3.10-slim-bookworm

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    libasound2 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel --no-cache-dir

# Copy requirements
COPY requirements.txt /tmp/requirements.txt

# Install python deps
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy app
WORKDIR /app
COPY . .

# Healthcheck
HEALTHCHECK CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "1200", "app:app"]
