FROM python:3.10-slim-bookworm

# ---------------------------------------------------------
# A) SYSTEM DEPENDENCIES
# ---------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    libasound2 \
    build-essential \
    libgomp1 \
    libgfortran5 \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------
# B) Upgrade pip
# ---------------------------------------------------------
RUN pip install --upgrade pip setuptools wheel --no-cache-dir

# ---------------------------------------------------------
# C) Install Python deps
# ---------------------------------------------------------
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ---------------------------------------------------------
# D) Copy application
# ---------------------------------------------------------
WORKDIR /app
COPY . .

# ---------------------------------------------------------
# E) Ensure temp storage exists
# ---------------------------------------------------------
RUN mkdir -p /tmp && chmod 777 /tmp

# ---------------------------------------------------------
# F) Healthcheck
# ---------------------------------------------------------
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:8080/health || exit 1

# ---------------------------------------------------------
# G) Run server
# ---------------------------------------------------------
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "1200", "app:app"]
