"""MinIO client — upload CSV bytes and return a presigned download URL."""
import boto3
from botocore.client import Config

from app.config import settings

_s3 = None


def get_s3():
    global _s3
    if _s3 is None:
        _s3 = boto3.client(
            "s3",
            endpoint_url=f"http{'s' if settings.minio_secure else ''}://{settings.minio_endpoint}",
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
        _ensure_bucket()
    return _s3


def _ensure_bucket():
    s3 = boto3.client(
        "s3",
        endpoint_url=f"http{'s' if settings.minio_secure else ''}://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )
    try:
        s3.head_bucket(Bucket=settings.minio_bucket)
    except Exception:
        s3.create_bucket(Bucket=settings.minio_bucket)


def upload_and_sign(key: str, data: bytes, content_type: str = "text/csv") -> str:
    """Upload *data* to MinIO under *key* and return a presigned GET URL."""
    s3 = get_s3()
    s3.put_object(
        Bucket=settings.minio_bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
        ContentDisposition=f'attachment; filename="{key.split("/")[-1]}"',
    )
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.minio_bucket, "Key": key},
        ExpiresIn=settings.report_presigned_ttl,
    )
    return url
