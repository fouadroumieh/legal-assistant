# app/services.py
from typing import List, Dict, Any
from uuid import uuid4
from fastapi import Depends, HTTPException
import httpx

from docapi.config import get_settings, Settings
from docapi.dependencies import (
    aws_clients as get_aws_clients,
    http_client as get_http_client,
)
from docapi.utils import sanitize_filename, scan_table_paginated
from docapi.filters import (
    build_filters_from_question,
    build_filters_from_nlp,
    build_nlp_context,
    matches,
)


class DocumentService:
    def __init__(
        self,
        aws_clients: Dict[str, Any] = Depends(get_aws_clients),
        settings: Settings = Depends(get_settings),
    ):
        self.s3 = aws_clients["s3"]
        self.docs_table = aws_clients["docs_table"]
        self.bucket = settings.docs_bucket

    async def list_documents(self, limit: int = 25) -> List[Dict[str, Any]]:
        if not self.docs_table:
            return []
        return await scan_table_paginated(self.docs_table, limit)

    def generate_presigned_url(self, filename: str) -> dict:
        key = f"uploads/{uuid4()}-{sanitize_filename(filename)}"
        presigned = self.s3.generate_presigned_post(
            Bucket=self.bucket,
            Key=key,
            ExpiresIn=300,
            Fields={},
            Conditions=[],
        )
        return {
            "bucket": self.bucket,
            "key": key,
            "url": presigned["url"],
            "fields": presigned["fields"],
        }

    async def get_dashboard_data(self) -> dict:
        if not self.docs_table:
            raise HTTPException(
                status_code=500, detail="DOCUMENTS_TABLE not configured"
            )

        agg = {
            "agreement_types": {},
            "jurisdictions": {},
            "industries": {},
        }

        def inc(bucket: dict, key: str):
            if key:
                bucket[key] = bucket.get(key, 0) + 1

        items = await scan_table_paginated(self.docs_table)
        for item in items:
            meta = item.get("metadata", {})
            inc(agg["agreement_types"], meta.get("agreement_type"))
            inc(
                agg["jurisdictions"],
                meta.get("governing_law") or meta.get("jurisdiction"),
            )
            inc(agg["industries"], meta.get("industry"))

        return {"ok": True, **agg}


class QueryService:
    def __init__(
        self,
        aws_clients: Dict[str, Any] = Depends(get_aws_clients),
        http_client: httpx.AsyncClient = Depends(get_http_client),
        settings: Settings = Depends(get_settings),
    ):
        self.docs_table = aws_clients["docs_table"]
        self.http_client = http_client
        self.nlp_url = settings.nlp_url

    async def query_documents(self, question: str) -> dict:
        question = (question or "").strip()
        if not question:
            raise HTTPException(status_code=400, detail="Empty question provided")
        if not self.nlp_url:
            raise HTTPException(status_code=500, detail="NLP_URL not configured")

        # 1) user-entered filters
        q_filters = build_filters_from_question(question)

        # 2) nlp extraction
        try:
            nlp_payload = {"text": question, "context": build_nlp_context(question)}
            resp = await self.http_client.post(
                f"{self.nlp_url.rstrip('/')}/analyze", json=nlp_payload
            )
            resp.raise_for_status()
            nlp_raw = resp.json() or {}
        except httpx.HTTPError:
            nlp_raw = {}

        nlp_filters = build_filters_from_nlp(nlp_raw, min_conf=0.7)

        # 3) merge
        filters = {**nlp_filters, **q_filters}
        if not filters:
            return {"ok": True, "filters_applied": {}, "matches": []}

        # 4) scan + match
        items = await scan_table_paginated(self.docs_table)
        results = []
        for item in items:
            meta = item.get("metadata", {}) or {}
            if matches(meta, filters):
                results.append(
                    {
                        "document": item.get("s3Key"),
                        "governing_law": meta.get("governing_law"),
                        "agreement_type": meta.get("agreement_type"),
                        "industry": meta.get("industry"),
                    }
                )

        return {"ok": True, "filters_applied": filters, "matches": results}
