FROM python:3.10-slim-bookworm

# ---------------------------------------------------------
# A) SYSTEM DEPENDENCIES (minimal + cleanup)
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
# B) PIP TOOLING
# ---------------------------------------------------------
RUN pip install --upgrade pip setuptools wheel --no-cache-dir

# ---------------------------------------------------------
# C) CACHED WHEEL DIRECTORY
# ---------------------------------------------------------
RUN mkdir -p /pipcache

# ---------------------------------------------------------
# D) INSTALL PYTHON DEPENDENCIES
# ---------------------------------------------------------
COPY requirements.txt /tmp/requirements.txt

ENV CFLAGS="-O3"
ENV BLAS=OpenBLAS
ENV LAPACK=OpenBLAS

RUN pip install --no-cache-dir --find-links=/pipcache --cache-dir=/pipcache \
    -r /tmp/requirements.txt

# ---------------------------------------------------------
# E) COPY PROJECT
# ---------------------------------------------------------
WORKDIR /app
COPY . .

# ---------------------------------------------------------
# F) CLEANUP — reduce image by 300–500 MB
# ---------------------------------------------------------
RUN find /usr/local/lib/python3.10 -type d -name "__pycache__" -exec rm -rf {} + && \
    find /usr/local/lib/python3.10 -type f -name "*.a" -delete && \
    find /usr/local/lib/python3.10 -type f -name "*.o" -delete && \
    find /usr/local/lib/python3.10 -type f -name "*.pyc" -delete && \
    rm -rf /root/.cache/pip/* && \
    rm -rf /pipcache/* && \
    rm -rf /usr/share/doc/* && \
    rm -rf /usr/share/man/*

# ---------------------------------------------------------
# G) Ensure /tmp is writable
# ---------------------------------------------------------
RUN mkdir -p /tmp && chmod 777 /tmp

# ---------------------------------------------------------
# H) HEALTHCHECK
# ---------------------------------------------------------
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:8080/health || exit 1

# ---------------------------------------------------------
# I) PORT + ENTRYPOINT
# ---------------------------------------------------------
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "1200", "app:app"]
