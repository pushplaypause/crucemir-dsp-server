FROM python:3.10-slim-bookworm

# ---------------------------------------------------------
# A) SYSTEM DEPENDENCIES (Render Safe)
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
    libsamplerate0-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------
# B) PIP UPGRADE
# ---------------------------------------------------------
RUN pip install --upgrade pip setuptools wheel --no-cache-dir

# ---------------------------------------------------------
# C) INSTALL PYTHON DEPENDENCIES
# ---------------------------------------------------------
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ---------------------------------------------------------
# D) COPY APPLICATION
# ---------------------------------------------------------
WORKDIR /app
COPY . .

# ---------------------------------------------------------
# E) CLEANUP
# ---------------------------------------------------------
RUN rm -rf /root/.cache && \
    rm -rf /usr/share/doc/* /usr/share/man/*

# ---------------------------------------------------------
# F) HEALTHCHECK
# ---------------------------------------------------------
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:8080/health || exit 1

# ---------------------------------------------------------
# G) PORT + GUNICORN
# ---------------------------------------------------------
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "1200", "app:app"]
