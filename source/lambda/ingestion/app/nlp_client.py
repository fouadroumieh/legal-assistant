
import json
import time
import urllib.request
import logging
from typing import Dict, Any
from . import config

logger = logging.getLogger(__name__)

def call_nlp_service(text: str) -> Dict[str, Any]:
    if not config.NLP_URL:
        logger.info("NLP_URL not set; skipping NLP")
        return {}
    url = config.NLP_URL.rstrip("/") + "/analyze"
    payload = json.dumps({"text": (text or "")[:200000]}).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8")
    dt = (time.time() - t0) * 1000
    logger.info("NLP call %s took %.1f ms", url, dt)
    result = json.loads(body)
    return result
