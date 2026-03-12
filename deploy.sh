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

echo "==> Building frontend..."
cd frontend && npm run build && cd ..

echo "==> Copying frontend build to static/..."
rm -rf static
cp -r frontend/dist static

echo "==> Building container image..."
gcloud builds submit --tag "$IMAGE" --project "$PROJECT_ID"

echo "==> Deploying to Cloud Run..."
gcloud run deploy "$SERVICE" \
  --image "$IMAGE" \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 1 \
  --min-instances 0 \
  --max-instances 3 \
  --set-env-vars "GOOGLE_API_KEY=${GOOGLE_API_KEY:-}" \
  --set-env-vars "DEMO_SECRET=${DEMO_SECRET:-}" \
  --set-env-vars "MUSIC_DIR=./music"

echo "==> Deployed successfully!"
gcloud run services describe "$SERVICE" --region "$REGION" --project "$PROJECT_ID" --format 'value(status.url)'
