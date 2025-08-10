
import io
import zipfile
from typing import Dict, Any, Tuple
import logging
from . import config

logger = logging.getLogger(__name__)

def read_s3_object(bucket: str, key: str) -> Tuple[bytes, Dict[str, Any]]:
    head = config.s3.head_object(Bucket=bucket, Key=key)
    obj = config.s3.get_object(Bucket=bucket, Key=key)
    body = obj["Body"].read()
    meta = {
        "size": head.get("ContentLength", 0),
        "contentType": head.get("ContentType") or "",
        "lastModified": (
            head.get("LastModified").isoformat() if head.get("LastModified") else None
        ),
        "etag": head.get("ETag"),
    }
    return body, meta

def is_text_artifact(key: str) -> bool:
    return key.startswith(config.TEXT_PREFIX) or key.endswith(".txt")

def build_text_key(original_key: str) -> str:
    k = original_key
    if k.startswith(config.TEXT_PREFIX):
        k = k[len(config.TEXT_PREFIX):]
    if k.endswith(".txt"):
        k = k[:-4]
    return f"{config.TEXT_PREFIX}{k}.txt"

def save_text_to_s3(bucket: str, original_key: str, text: str) -> str:
    text_key = build_text_key(original_key)
    config.s3.put_object(
        Bucket=bucket,
        Key=text_key.replace("uploads/", ""),
        Body=text.encode("utf-8"),
        ContentType="text/plain; charset=utf-8",
        CacheControl="no-cache",
    )
    logger.info("Saved extracted text: s3://%s/%s", bucket, text_key)
    return text_key
