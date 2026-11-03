"""Helpers for the optional direct-to-S3 upload demo."""

from importlib.util import find_spec

from django.conf import settings

# Browser origins that may upload to the bucket: the runserver addresses.
DEFAULT_CORS_ORIGINS = ["http://127.0.0.1:8000", "http://localhost:8000"]


def s3_uploads_enabled() -> bool:
    """True when the S3 extras are installed and a bucket is configured."""
    return bool(settings.AWS_STORAGE_BUCKET_NAME) and all(
        find_spec(name) is not None for name in ("boto3", "storages")
    )


def cors_configuration(origins: list[str]) -> dict:
    """
    The CORS rule the browser needs for multipart uploads.

    The widget PUTs each part to a presigned URL on the bucket's host, then
    reads the part's ``ETag`` response header to complete the upload, so
    ``ETag`` must be exposed to JavaScript.
    """
    return {
        "CORSRules": [
            {
                "AllowedOrigins": origins,
                "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
                "AllowedHeaders": ["*"],
                "ExposeHeaders": ["ETag"],
                "MaxAgeSeconds": 3600,
            }
        ]
    }
