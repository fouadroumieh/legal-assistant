from fastapi import FastAPI
from .config import get_settings
from .models import AnalyzeIn, AnalyzeOut
from .services import AnalyzerService

app = FastAPI()
svc = AnalyzerService()  # single instance; models are cached in dependencies


@app.get("/health")
def health():
    s = get_settings()
    return {"ok": True, "embed_model": s.embed_model_name}


@app.post("/analyze", response_model=AnalyzeOut)
def analyze(payload: AnalyzeIn):
    result = svc.analyze(payload.text)
    return AnalyzeOut(**result)
