FROM python:3.10-slim-bookworm

# ---------------------------------------------------------
# SYSTEM DEPENDENCIES (Only what your DSP server uses)
# ---------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    libsndfile1 \
    libasound2 \
    libgomp1 \
    build-essential \
    liblapack-dev \
    libblas-dev \
    libeigen3-dev \
    libsamplerate0-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------
# PIP UPGRADE
# ---------------------------------------------------------
RUN pip install --upgrade pip setuptools wheel

# ---------------------------------------------------------
# INSTALL PYTHON DEPS
# ---------------------------------------------------------
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ---------------------------------------------------------
# COPY APP
# ---------------------------------------------------------
WORKDIR /app
COPY . .

# ---------------------------------------------------------
# MAKE /tmp WRITABLE
# ---------------------------------------------------------
RUN mkdir -p /tmp && chmod 777 /tmp

# ---------------------------------------------------------
# HEALTHCHECK
# ---------------------------------------------------------
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://localhost:8080/health || exit 1

# ---------------------------------------------------------
# GUNICORN
# ---------------------------------------------------------
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "1200", "app:app"]
