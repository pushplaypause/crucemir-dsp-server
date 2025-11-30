FROM python:3.10-slim-bookworm

# ---------------------------------------------------------
# A) SYSTEM DEPENDENCIES (DSP + Torch + FFmpeg)
# ---------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    libsndfile1 \
    libsndfile1-dev \
    libasound2 \
    build-essential \
    libfftw3-dev \
    liblapack-dev \
    libblas-dev \
    libeigen3-dev \
    libyaml-dev \
    libtag1-dev \
    libsamplerate0-dev \
    libgomp1 \
    libgfortran5 \
    libjpeg-dev \
    zlib1g-dev \
    pkg-config \
    wget \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------
# B) Upgrade pip + tools
# ---------------------------------------------------------
RUN pip install --upgrade pip setuptools wheel --no-cache-dir

# ---------------------------------------------------------
# C) Install Python dependencies
# ---------------------------------------------------------
COPY requirements.txt /tmp/requirements.txt
ENV CFLAGS="-O3"

# ⚡ CRITICAL: Clean install — no caches, no wheel re-use
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ---------------------------------------------------------
# D) Copy Application
# ---------------------------------------------------------
WORKDIR /app
COPY . .

# ---------------------------------------------------------
# E) Cleanup — shrink image by ~40%
# ---------------------------------------------------------
RUN find /usr/local/lib/python3.10 -type d -name "__pycache__" -exec rm -rf {} + && \
    find /usr/local/lib/python3.10 -type f -name "*.pyc" -delete && \
    find /usr/local/lib/python3.10 -type f -name "*.a" -delete && \
    find /usr/local/lib/python3.10 -type f -name "*.o" -delete && \
    rm -rf /root/.cache/pip/* && \
    rm -rf /usr/share/doc/* && \
    rm -rf /usr/share/man/*

# ---------------------------------------------------------
# F) Ensure /tmp is writable
# ---------------------------------------------------------
RUN mkdir -p /tmp && chmod 777 /tmp

# ---------------------------------------------------------
# G) Healthcheck
# ---------------------------------------------------------
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:8080/health || exit 1

# ---------------------------------------------------------
# H) Start Gunicorn
# ---------------------------------------------------------
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "1200", "app:app"]
