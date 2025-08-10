# app/dependencies.py
from typing import Dict, Any, AsyncIterator
from functools import lru_cache
import boto3
from botocore.config import Config
import httpx
from fastapi import Depends
from .config import get_settings, Settings


@lru_cache()
def _boto3_clients() -> Dict[str, Any]:
    settings: Settings = get_settings()
    s3 = boto3.client(
        "s3",
        region_name=settings.docs_bucket_region,
        config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
    )
    dynamodb = boto3.resource("dynamodb", region_name=settings.docs_bucket_region)
    docs_table = (
        dynamodb.Table(settings.documents_table) if settings.documents_table else None
    )
    return {"s3": s3, "docs_table": docs_table}


def aws_clients() -> Dict[str, Any]:
    return _boto3_clients()


async def http_client() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(timeout=15) as client:
        yield client
