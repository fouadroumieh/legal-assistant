import os
import time
import uuid
import logging
import urllib.parse
from typing import Dict, Any
from . import config
from .s3_io import read_s3_object, is_text_artifact, build_text_key, save_text_to_s3
from .extractors import normalize_ext, extract_text
from .nlp_client import call_nlp_service
from .heuristics import first_date, guess_title
from .persistence import write_documents_table, to_metadata_map

logger = logging.getLogger(__name__)


def process_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    bucket = rec["bucket"]
    key_raw = rec["key"]
    key = urllib.parse.unquote_plus(key_raw)
    logger.info("Processing s3://%s/%s (raw=%s)", bucket, key, key_raw)

    if is_text_artifact(key):
        logger.info("Skipping extracted/text artifact key: %s", key)
        return {"documentId": None, "key": key, "status": "SKIPPED"}

    etime = rec.get("eventTime") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    try:
        data, head = read_s3_object(bucket, key)
        ext = normalize_ext(key)
        logger.info(
            "Head: size=%s contentType=%s ext=%s",
            head.get("size"),
            head.get("contentType"),
            ext,
        )

        text, page_count = extract_text(data, ext)
        logger.info("Extracted text length=%d", len(text))
        text_key = save_text_to_s3(bucket, key, text) if text else None

        nlp = {}
        try:
            if text:
                nlp = call_nlp_service(text)
            else:
                logger.warning("No text extracted; skipping NLP")
        except Exception as e:
            logger.warning("NLP error: %s", e)
            nlp = {"_nlp_error": str(e)}

        title = (
            (nlp.get("title") or guess_title(text) or os.path.basename(key))
            if text
            else os.path.basename(key)
        )
        eff_date = nlp.get("effective_date") or first_date(text)
        govlaw = nlp.get("governing_law")
        ag_type = nlp.get("agreement_type")
        industry = nlp.get("industry")
        parties = nlp.get("parties") or []

        document_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"s3://{bucket}/{key}"))

        doc_item = {
            "documentId": document_id,
            "bucket": bucket,
            "s3Key": key,
            "mimeType": head.get("contentType"),
            "size": head.get("size"),
            "pageCount": page_count,
            "textKey": text_key,
            "createdAt": etime,
            "lastModified": head.get("lastModified"),
            "etag": head.get("etag"),
            "nlpVersion": "oss-v1",
        }
        write_documents_table(doc_item)

        meta_fields = {
            "title": title,
            "agreement_type": ag_type,
            "agreement_type_confidence": nlp.get("agreement_type_confidence"),
            "governing_law": govlaw,
            "governing_law_confidence": nlp.get("governing_law_confidence"),
            "effective_date": eff_date,
            "industry": industry,
            "industry_confidence": nlp.get("industry_confidence"),
            "parties": parties,
            "ingestion_status": (
                "OK" if not nlp.get("_nlp_error") else f"NLP_ERROR: {nlp['_nlp_error']}"
            ),
        }

        config.doc_table.update_item(
            Key={"documentId": document_id},
            UpdateExpression="SET #m = :m",
            ExpressionAttributeNames={"#m": "metadata"},
            ExpressionAttributeValues={":m": to_metadata_map(meta_fields)},
        )

        return {"documentId": document_id, "key": key, "status": "OK"}

    except Exception as e:
        logger.exception("Ingestion error for key=%s: %s", key, e)
        document_id = str(uuid.uuid4())
        return {"documentId": document_id, "key": key, "status": f"ERROR: {e}"}
