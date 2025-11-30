FROM python:3.10-slim-bookworm

# ---------------------------------------------------------
# A) SYSTEM DEPENDENCIES
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
# B) Upgrade pip tools
# ---------------------------------------------------------
RUN pip install --upgrade pip setuptools wheel --no-cache-dir

# ---------------------------------------------------------
# C) Install Python dependencies
# ---------------------------------------------------------
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ---------------------------------------------------------
# D) Copy app
# ---------------------------------------------------------
WORKDIR /app
COPY . .

# ---------------------------------------------------------
# E) Cleanup to shrink image ~35-45%
# ---------------------------------------------------------
RUN find /usr/local/lib/python3.10 -type d -name "__pycache__" -exec rm -rf {} + && \
    rm -rf /root/.cache/pip/* && \
    rm -rf /usr/share/doc/* && \
    rm -rf /usr/share/man/*

# ---------------------------------------------------------
# F) Ensure /tmp is writable
# ---------------------------------------------------------
RUN mkdir -p /tmp && chmod 777 /tmp

# ---------------------------------------------------------
# G) HEALTHCHECK
# ---------------------------------------------------------
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:8080/health || exit 1

# ---------------------------------------------------------
# H) Gunicorn
# ---------------------------------------------------------
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "1200", "app:app"]
