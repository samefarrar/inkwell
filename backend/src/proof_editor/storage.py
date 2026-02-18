"""Google Cloud Storage integration for file uploads."""

import logging
import os
import uuid
from pathlib import PurePosixPath

logger = logging.getLogger(__name__)

BUCKET_NAME = "inkwell-uploads"

_client = None


def _get_client():
    """Lazy-initialize GCS client. Returns None if credentials not configured."""
    global _client
    if _client is not None:
        return _client

    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        logger.info("GOOGLE_APPLICATION_CREDENTIALS not set — GCS disabled")
        return None

    try:
        from google.cloud import storage

        _client = storage.Client()
        return _client
    except Exception as e:
        logger.warning("Failed to initialize GCS client: %s", e)
        return None


def upload_to_gcs(
    data: bytes,
    style_id: int,
    filename: str,
    content_type: str,
) -> str | None:
    """Upload file bytes to GCS. Returns gs:// URI or None if GCS disabled."""
    client = _get_client()
    if client is None:
        return None

    safe_stem = PurePosixPath(filename).stem[:50]
    ext = PurePosixPath(filename).suffix.lower()
    uid = uuid.uuid4().hex[:12]
    blob_name = f"styles/{style_id}/{uid}_{safe_stem}{ext}"

    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(data, content_type=content_type)

    return f"gs://{BUCKET_NAME}/{blob_name}"
