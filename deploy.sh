#!/usr/bin/env bash
# CutTo — deploy to Google Cloud Run
# Usage: ./deploy.sh [PROJECT_ID]
set -euo pipefail

PROJECT_ID="${1:-$(gcloud config get-value project 2>/dev/null)}"
REGION="us-central1"
SERVICE="cutto"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE}"

if [ -z "$PROJECT_ID" ]; then
  echo "Usage: ./deploy.sh <GCP_PROJECT_ID>"
  exit 1
fi

echo "==> Building container image (multi-stage: frontend + backend)..."
gcloud builds submit --tag "$IMAGE" --project "$PROJECT_ID" --timeout=1800

echo "==> Deploying to Cloud Run..."
gcloud run deploy "$SERVICE" \
  --image "$IMAGE" \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --platform managed \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 4 \
  --timeout 900 \
  --concurrency 1 \
  --min-instances 0 \
  --max-instances 2 \
  --session-affinity \
  --set-env-vars "GOOGLE_API_KEY=${GOOGLE_API_KEY:-}" \
  --set-env-vars "DEMO_SECRET=${DEMO_SECRET:-}" \
  --set-env-vars "MUSIC_DIR=./music" \
  --set-env-vars "GCS_BUCKET=${GCS_BUCKET:-}" \
  --set-env-vars "PIPELINE_PARALLEL_BATCH_SIZE=${PIPELINE_PARALLEL_BATCH_SIZE:-1}" \
  --set-env-vars "SCENE_TIMEOUT_SECONDS=${SCENE_TIMEOUT_SECONDS:-420}" \
  --set-env-vars "WAV2LIP_TIMEOUT_SECONDS=${WAV2LIP_TIMEOUT_SECONDS:-600}" \
  --set-env-vars "WAV2LIP_FACE_DET_BATCH_SIZE=${WAV2LIP_FACE_DET_BATCH_SIZE:-4}" \
  --set-env-vars "WAV2LIP_INFER_BATCH_SIZE=${WAV2LIP_INFER_BATCH_SIZE:-16}"

echo "==> Deployed successfully!"
gcloud run services describe "$SERVICE" --region "$REGION" --project "$PROJECT_ID" --format 'value(status.url)'
