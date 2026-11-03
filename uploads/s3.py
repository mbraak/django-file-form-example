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


def upload_prefix(s3_upload_dir: str) -> str:
    """The key prefix django-file-form uploads to: ``temp_uploads/<dir>/``."""
    upload_dir = getattr(settings, "FILE_FORM_UPLOAD_DIR", "temp_uploads")
    return f"{upload_dir}/{s3_upload_dir}/"


def list_uploaded_files(s3_upload_dir: str, limit: int = 50) -> list[dict]:
    """
    The objects the widget uploaded for ``s3_upload_dir``, newest first.

    The bucket is private, so each file gets a short-lived presigned download
    URL that Django signs. The browser fetches the file straight from S3, just
    as it uploaded it.
    """
    from django_file_form.s3_multipart.utils import get_bucket_name, get_client

    client = get_client()
    bucket = get_bucket_name()
    prefix = upload_prefix(s3_upload_dir)
    response = client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=1000)
    objects = sorted(
        response.get("Contents", []), key=lambda o: o["LastModified"], reverse=True
    )

    return [
        {
            "name": obj["Key"].removeprefix(prefix),
            "key": obj["Key"],
            "size": obj["Size"],
            "last_modified": obj["LastModified"],
            "url": client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": obj["Key"]},
                ExpiresIn=300,
            ),
        }
        for obj in objects[:limit]
    ]


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
