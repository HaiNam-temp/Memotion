# Stage 1: Build dependencies
FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Update and install system dependencies required for building python packages
# gcc and build-essential are often needed for numpy, pandas, etc.
# libpq-dev is needed to build psycopg2
# FFmpeg libraries and pkg-config are needed for PyAV (av package)
# OpenCV and MediaPipe dependencies
# Note: libgl1 works on both Debian 12 and Ubuntu 24.04
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev build-essential \
    ffmpeg libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev \
    libavfilter-dev libswscale-dev libswresample-dev pkg-config \
    libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    libgtk-3-0 libgdk-pixbuf-2.0-0 libcairo-gobject2 libpango-1.0-0 libatk1.0-0 libcairo2 \
    libgl1 libglx-mesa0 libglvnd0 libegl1 && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY app/requirements.txt .

# Upgrade pip and create wheels for dependencies
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt


# Stage 2: Runtime image
FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# MediaPipe/OpenCV environment variables
ENV PYTHONPATH="/app:/app/app/mediapipe/mediapipe_be:${PYTHONPATH}"
ENV POSE_DETECTION_ENABLED=true
ENV QT_QPA_PLATFORM=offscreen
ENV MPLBACKEND=Agg

# Install runtime libraries for postgres (libpq5) and MediaPipe/OpenCV
# Note: libgl1 works on both Debian 12 and Ubuntu 24.04
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 ffmpeg curl \
    libglib2.0-0 libsm6 libxext6 libxrender1 libgomp1 \
    libgtk-3-0 libgdk-pixbuf-2.0-0 libcairo-gobject2 libpango-1.0-0 libatk1.0-0 libcairo2 \
    libgl1 libglx-mesa0 libglvnd0 libegl1 && \
    rm -rf /var/lib/apt/lists/*

# Copy wheels and requirements from builder stage
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# Install dependencies from wheels
RUN pip install --no-cache /wheels/*

# Copy the rest of the application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/static/uploads/exercise \
    /app/logs \
    /app/models

# Set environment variables
ENV PORT=8005
ENV HOST=0.0.0.0

# Expose the port the app runs on
EXPOSE 8005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8005/health || exit 1

# Command to run the application with MediaPipe support
CMD ["python", "-m", "app.main"]
