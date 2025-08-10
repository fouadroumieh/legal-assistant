# docapi/main.py
from typing import List, Dict, Any

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from docapi.config import get_settings
from docapi.services import DocumentService, QueryService
from docapi.models import (
    PresignBody,
    PresignResponse,
    QueryIn,
    QueryResponse,
    DashboardResponse,
)

app = FastAPI(docs_url="/api-docs", redoc_url=None, openapi_url="/openapi.json")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in prod
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    s = get_settings()
    return {"ok": True, "region": s.docs_bucket_region, "nlp_url": s.nlp_url}


@app.get("/docs")
async def list_docs(svc: DocumentService = Depends()) -> List[Dict[str, Any]]:
    return await svc.list_documents(limit=25)


@app.post("/upload/presign", response_model=PresignResponse)
def presign(body: PresignBody, svc: DocumentService = Depends()):
    filename = (body.filename or "upload.bin").strip() or "upload.bin"
    return svc.generate_presigned_url(filename)


@app.post("/query", response_model=QueryResponse)
async def query(payload: QueryIn, svc: QueryService = Depends()):
    return await svc.query_documents(payload.question)


@app.get("/dashboard", response_model=DashboardResponse)
async def dashboard(svc: DocumentService = Depends()):
    return await svc.get_dashboard_data()
