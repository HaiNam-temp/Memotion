# Stage 1: Build dependencies
FROM python:3.10-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Update and install system dependencies required for building python packages
# gcc and build-essential are often needed for numpy, pandas, etc.
# libpq-dev is needed to build psycopg2
# FFmpeg libraries and pkg-config are needed for PyAV (av package)
# OpenCV and MediaPipe dependencies: libglib2.0-0, libsm6, libxext6, libxrender-dev, libgomp1, libgthread-2.0-0
# Additional for MediaPipe: libgtk-3-0, libgdk-pixbuf-2.0-0, libcairo-gobject2, libpango-1.0-0, libatk1.0-0, libcairo2
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev build-essential \
    ffmpeg libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev \
    libavfilter-dev libswscale-dev libswresample-dev pkg-config \
    libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 libgthread-2.0-0 \
    libgtk-3-0 libgdk-pixbuf-2.0-0 libcairo-gobject2 libpango-1.0-0 libatk1.0-0 libcairo2 && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY app/requirements.txt .

# Upgrade pip and create wheels for dependencies
# Creating wheels allows us to compile once and install quickly in the next stage
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt


# Stage 2: Runtime image
FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install runtime libraries for postgres (libpq5) and MediaPipe/OpenCV
# We don't need gcc or build tools here, keeping the image small
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 \
    libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 libgthread-2.0-0 \
    libgtk-3-0 libgdk-pixbuf-2.0-0 libcairo-gobject2 libpango-1.0-0 libatk1.0-0 libcairo2 && \
    rm -rf /var/lib/apt/lists/*

# Copy wheels and requirements from builder stage
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# Install dependencies from wheels
RUN pip install --no-cache /wheels/*

# Copy the rest of the application code
COPY . .

# Set environment variables
ENV PORT=8005
ENV POSE_DETECTION_ENABLED=true

# Expose the port the app runs on
EXPOSE 8005

# Command to run the application
CMD ["python", "-m", "app.main"]
