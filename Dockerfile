FROM python:3.10-slim-bookworm

# ---------------------------------------------------------
# A) SYSTEM DEPENDENCIES (NO FFMPEG DEV, ONLY RUNTIME)
# ---------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    libsndfile1 \
    libasound2 \
    libgomp1 \
    libgfortran5 \
    libsamplerate0 \
    libyaml-dev \
    libeigen3-dev \
    liblapack-dev \
    libblas-dev \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------
# B) UPGRADE PIP
# ---------------------------------------------------------
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# ---------------------------------------------------------
# C) COPY REQUIREMENTS
# ---------------------------------------------------------
COPY requirements.txt /tmp/requirements.txt

# ---------------------------------------------------------
# D) INSTALL PYTHON DEPENDENCIES
# ---------------------------------------------------------
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ---------------------------------------------------------
# E) COPY FULL APP
# ---------------------------------------------------------
WORKDIR /app
COPY . .

# ---------------------------------------------------------
# F) CLEANUP (SHRINK IMAGE ~30%)
# ---------------------------------------------------------
RUN find /usr/local/lib/python3.10 -type d -name "__pycache__" -exec rm -rf {} + && \
    rm -rf /root/.cache/pip/*

# ---------------------------------------------------------
# G) ENSURE TMP IS WRITABLE (Render requirement)
# ---------------------------------------------------------
RUN mkdir -p /tmp && chmod 777 /tmp

# ---------------------------------------------------------
# H) HEALTHCHECK
# ---------------------------------------------------------
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:8080/health || exit 1

# ---------------------------------------------------------
# I) GUNICORN SERVER
# ---------------------------------------------------------
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "1200", "app:app"]
