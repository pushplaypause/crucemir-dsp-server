FROM python:3.10-slim

# ---------------------------------------------------------
# SYSTEM DEPENDENCIES (DSP + Torch + FFmpeg)
# ---------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    libsndfile1 \
    libsndfile1-dev \
    build-essential \
    libfftw3-dev \
    liblapack-dev \
    libblas-dev \
    libeigen3-dev \
    libyaml-dev \
    libtag1-dev \
    libsamplerate0-dev \
    libgomp1 \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*


# ---------------------------------------------------------
# PYTHON BUILD TOOLING (prevents SciPy/Numpy compile errors)
# ---------------------------------------------------------
RUN pip install --upgrade pip setuptools wheel


# ---------------------------------------------------------
# INSTALL PYTHON DEPENDENCIES
# ---------------------------------------------------------
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt


# ---------------------------------------------------------
# COPY APP
# ---------------------------------------------------------
WORKDIR /app
COPY . .


# ---------------------------------------------------------
# EXPOSE PORT & RUN GUNICORN
# ---------------------------------------------------------
EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "1200", "app:app"]
