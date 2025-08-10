import pytest
from fastapi.testclient import TestClient

import docapi.main as main_mod
from docapi.main import app
from docapi.services import DocumentService, QueryService


# ---------- helpers / fakes ----------


class FakeSettings:
    docs_bucket_region = "eu-central-1"
    nlp_url = "http://nlp.local"


class MockDocumentService:
    def __init__(self, *args, **kwargs):
        pass

    async def list_documents(self, limit: int = 25):
        # return a small, realistic shape
        return [
            {"s3Key": "doc1.pdf", "metadata": {"agreement_type": "NDA"}},
            {"s3Key": "doc2.pdf", "metadata": {"agreement_type": "MSA"}},
        ]

    def generate_presigned_url(self, filename: str):
        return {
            "bucket": "my-bucket",
            "key": f"uploads/uuid-{filename}",
            "url": "https://s3.example.com",
            "fields": {"key": "value"},
        }

    async def get_dashboard_data(self):
        return {
            "ok": True,
            "agreement_types": {"NDA": 2, "MSA": 1},
            "jurisdictions": {"US": 2, "DE": 1},
            "industries": {"Tech": 3},
        }


class MockQueryService:
    def __init__(self, *args, **kwargs):
        pass

    async def query_documents(self, question: str):
        return {
            "ok": True,
            "filters_applied": {"agreement_type": "NDA"},
            "matches": [
                {
                    "document": "doc1.pdf",
                    "governing_law": "US",
                    "agreement_type": "NDA",
                    "industry": "Tech",
                }
            ],
        }


@pytest.fixture(autouse=True)
def _override_settings(monkeypatch):
    # make /health deterministic without env
    monkeypatch.setattr(main_mod, "get_settings", lambda: FakeSettings())
    yield


@pytest.fixture
def client():
    # clear & set dependency overrides fresh for each test
    app.dependency_overrides.clear()
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------- tests ----------


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["region"] == "eu-central-1"
    assert data["nlp_url"] == "http://nlp.local"


def test_list_docs(client):
    app.dependency_overrides[DocumentService] = lambda: MockDocumentService()
    r = client.get("/docs")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert data[0]["s3Key"] == "doc1.pdf"


def test_presign(client):
    app.dependency_overrides[DocumentService] = lambda: MockDocumentService()
    r = client.post("/upload/presign", json={"filename": "file.bin"})
    assert r.status_code == 200
    data = r.json()
    # response_model ensures these keys exist
    assert data["bucket"] == "my-bucket"
    assert data["url"]
    assert data["fields"]
    assert data["key"].endswith("file.bin")


def test_query(client):
    app.dependency_overrides[QueryService] = lambda: MockQueryService()
    r = client.post("/query", json={"question": "find nda"})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["filters_applied"]["agreement_type"] == "NDA"
    assert data["matches"][0]["document"] == "doc1.pdf"


def test_dashboard(client):
    app.dependency_overrides[DocumentService] = lambda: MockDocumentService()
    r = client.get("/dashboard")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["agreement_types"]["NDA"] == 2
