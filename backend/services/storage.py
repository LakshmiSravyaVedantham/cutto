"""Google Cloud Storage service for persisting generated videos."""

import logging
import os
from datetime import timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

GCS_BUCKET = os.environ.get("GCS_BUCKET", "")

_gcs_available = False
try:
    from google.cloud import storage as gcs

    if GCS_BUCKET:
        _gcs_available = True
        logger.info(f"GCS available — bucket: {GCS_BUCKET}")
    else:
        logger.info("GCS_BUCKET not set — videos served locally only")
except ImportError:
    logger.info("google-cloud-storage not installed — videos served locally only")


def is_available() -> bool:
    """Check if GCS is configured and available."""
    return _gcs_available


def upload_video(local_path: str, video_id: str) -> str:
    """Upload video to GCS and return a signed URL (valid 1 hour).

    Returns the local path unchanged if GCS is not available.
    """
    if not _gcs_available:
        return local_path

    try:
        client = gcs.Client()
        bucket = client.bucket(GCS_BUCKET)
        blob_name = f"videos/{video_id}/final.mp4"
        blob = bucket.blob(blob_name)

        logger.info(f"Uploading {local_path} to gs://{GCS_BUCKET}/{blob_name}")
        blob.upload_from_filename(local_path, content_type="video/mp4")

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(hours=1),
            method="GET",
        )
        logger.info(f"Upload complete — signed URL generated")
        return url
    except Exception as e:
        logger.warning(f"GCS upload failed ({e}), serving locally")
        return local_path
