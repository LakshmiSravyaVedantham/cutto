# CutTo Deploy Checklist

## Prerequisites
- [ ] Google Cloud account with billing enabled
- [ ] `gcloud` CLI installed (already at `/opt/homebrew/share/google-cloud-sdk/bin/gcloud`)
- [ ] Google AI Studio API key with Gemini, Veo, and Imagen access

## Step 1: Authenticate
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

## Step 2: Enable APIs
```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

## Step 3: Set environment variables
```bash
export GOOGLE_API_KEY=your-api-key
export DEMO_SECRET=your-demo-password  # optional
export GCS_BUCKET=                      # optional
```

## Step 4: Deploy
```bash
cd /Users/sravyalu/cutto
./deploy.sh YOUR_PROJECT_ID
```

This will:
1. Build multi-stage Docker image (frontend + backend) via Cloud Build
2. Deploy to Cloud Run (2 vCPU, 2GB RAM, 5min timeout)
3. Print the live URL

## Step 5: Verify
- [ ] Open the Cloud Run URL in browser
- [ ] Landing page loads with tech badges
- [ ] Click "Start Creating" — WebSocket connects
- [ ] Type a video idea — Gemini responds with preview images
- [ ] Scene plan appears in editor
- [ ] Approve and verify pipeline starts
- [ ] Video generates and plays

## Step 6: Record GCP proof
- [ ] Open Google Cloud Console > Cloud Run
- [ ] Show the cutto service running
- [ ] Take a screen recording (needed for Devpost submission)

## Step 7: Set DEMO_SECRET for judges
If using demo gate:
```bash
gcloud run services update cutto \
  --region us-central1 \
  --set-env-vars "DEMO_SECRET=judge-password"
```
Share the URL with `?key=judge-password` for judge access.
