from typing import List, Optional
from pydantic import BaseModel


class AnalyzeIn(BaseModel):
    text: str


class AnalyzeOut(BaseModel):
    title: Optional[str] = None
    effective_date: Optional[str] = None
    governing_law: Optional[str] = None
    governing_law_confidence: float = 0.0
    agreement_type: Optional[str] = None
    agreement_type_confidence: float = 0.0
    industry: Optional[str] = None
    industry_confidence: float = 0.0
    parties: List[str] = []
