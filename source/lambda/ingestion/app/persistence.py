
import json
import logging
from decimal import Decimal
from typing import Dict, Any
from . import config

logger = logging.getLogger(__name__)

def safe_val(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return Decimal(str(v))
    return v

def to_metadata_map(d: dict) -> dict:
    return {k: safe_val(v) for k, v in d.items()}

def to_dynamo_value(v):
    if isinstance(v, float):
        return Decimal(str(v))
    if isinstance(v, (str, int, bool)) or v is None:
        return v
    return json.dumps(v)

def write_documents_table(item: Dict[str, Any]) -> None:
    config.doc_table.put_item(Item=item)
    logger.info("Wrote DocumentsTable item documentId=%s", item["documentId"])
