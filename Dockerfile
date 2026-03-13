# Stage 1: Build frontend
FROM node:18-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Python backend + serve frontend
FROM python:3.11-slim
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg libglib2.0-0 libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    torch==2.10.0 \
    torchvision==0.25.0 && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend + music + Wav2Lip assets
COPY backend/ backend/
COPY music/ music/
COPY wav2lip_repo/ wav2lip_repo/

# Copy built frontend from stage 1
COPY --from=frontend /app/frontend/dist static/

EXPOSE 8080

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
