
import json
import logging
from . import config
from .events import records_from_event
from .processor import process_record

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    logger.info(
        "ENV DOCS_BUCKET=%s AWS_REGION=%s NLP_URL=%s",
        config.DOCS_BUCKET,
        config.AWS_REGION,
        config.NLP_URL,
    )
    try:
        logger.info("Event: %s", json.dumps(event)[:2000])
    except Exception:
        logger.info("Received event (unserializable)")

    records = records_from_event(event)
    logger.info("Parsed %d record(s) from event", len(records))
    if not records:
        return {"ok": False, "reason": "no-records"}

    processed = []
    for r in records:
        res = process_record(r)
        if res and res.get("status") != "SKIPPED":
            processed.append(res)

    logger.info("Processed %d record(s)", len(processed))
    return {"ok": True, "processed": processed}
