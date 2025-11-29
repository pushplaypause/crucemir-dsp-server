FROM python:3.10-slim

# System dependencies required for:
# - Essentia
# - Demucs
# - CREPE
# - Librosa
# - Torch CPU
# - FFMPEG processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    libsndfile1 \
    build-essential \
    libfftw3-dev \
    liblapack-dev \
    libblas-dev \
    libeigen3-dev \
    libyaml-dev \
    libtag1-dev \
    libsamplerate0-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /app
COPY . .

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "1200", "app:app"]
