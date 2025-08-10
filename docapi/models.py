from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class PresignBody(BaseModel):
    filename: Optional[str] = "upload.bin"


class PresignResponse(BaseModel):
    bucket: str
    key: str
    url: str
    fields: Dict[str, Any]


class QueryIn(BaseModel):
    question: str


class QueryMatch(BaseModel):
    document: Optional[str] = None
    governing_law: Optional[str] = None
    agreement_type: Optional[str] = None
    industry: Optional[str] = None


class QueryResponse(BaseModel):
    ok: bool
    filters_applied: Dict[str, Any]
    matches: List[QueryMatch]


class DashboardResponse(BaseModel):
    ok: bool
    agreement_types: Dict[str, int]
    jurisdictions: Dict[str, int]
    industries: Dict[str, int]
