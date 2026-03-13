"""Google Cloud Storage service for persisting generated videos."""

import logging
import os

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


def _blob_name(video_id: str) -> str:
    return f"videos/{video_id}/final.mp4"


def upload_video(local_path: str, video_id: str) -> bool:
    """Upload video to GCS.

    Returns True on success, False on failure or when GCS is unavailable.
    """
    if not _gcs_available:
        return False

    try:
        client = gcs.Client()
        bucket = client.bucket(GCS_BUCKET)
        blob_name = _blob_name(video_id)
        blob = bucket.blob(blob_name)

        logger.info(f"Uploading {local_path} to gs://{GCS_BUCKET}/{blob_name}")
        blob.upload_from_filename(local_path, content_type="video/mp4")
        logger.info("Upload complete")
        return True
    except Exception as e:
        logger.warning(f"GCS upload failed ({e}), serving locally")
        return False


def download_video(video_id: str) -> bytes | None:
    """Download a video from GCS as bytes."""
    if not _gcs_available:
        return None

    try:
        client = gcs.Client()
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(_blob_name(video_id))
        if not blob.exists():
            return None
        logger.info(f"Downloading gs://{GCS_BUCKET}/{blob.name}")
        return blob.download_as_bytes()
    except Exception as e:
        logger.warning(f"GCS download failed ({e})")
        return None
