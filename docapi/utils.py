# app/utils.py
import re
from typing import List, Dict, Any, Optional
from anyio import to_thread


def sanitize_filename(name: Optional[str]) -> str:
    if not name:
        return "upload.bin"
    return "".join(c for c in name if c.isalnum() or c in ("-", "_", ".", " "))[:200]


async def _scan_once(table, **kwargs) -> Dict[str, Any]:
    # boto3 is sync; run in a worker thread
    def _call():
        return table.scan(**kwargs)

    return await to_thread.run_sync(_call)


async def scan_table_paginated(
    table, limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Asynchronously scan a DynamoDB table with pagination.
    If `limit` is provided, returns up to that many items.
    """
    if not table:
        return []

    items: List[Dict[str, Any]] = []
    start_key = None

    while True:
        kwargs = {}
        if start_key:
            kwargs["ExclusiveStartKey"] = start_key
        resp = await _scan_once(table, **kwargs)
        batch = resp.get("Items", [])
        items.extend(batch)

        if limit is not None and len(items) >= limit:
            return items[:limit]

        start_key = resp.get("LastEvaluatedKey")
        if not start_key:
            break

    return items
