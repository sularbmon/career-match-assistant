"""Regression checks against PostgreSQL; every test rolls back its data."""
import pymupdf as fitz
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.session import engine, get_db
from app.models.knowledge import KnowledgeChunk
from app.services.vector_search import search_similar_chunks
from app.services.skill_extractor import extract_skills


@pytest.fixture
def db():
    with engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            session.close()
            transaction.rollback()


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_resume_to_recommendations(client, monkeypatch):
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Python developer with FastAPI and PostgreSQL experience")
    pdf = document.tobytes()
    document.close()
    uploaded = client.post("/api/v1/resume/upload", files={
        "file": ("test.pdf", pdf, "application/pdf")
    })
    assert uploaded.status_code == 201, uploaded.text
    resume = uploaded.json()
    from app.api.resume import UPLOAD_DIR
    try:
        job = client.post("/api/v1/jobs/analyze", json={
            "job_description": "Seeking Python FastAPI developer with AWS experience"
        })
        assert job.status_code == 201, job.text
        matched = client.post("/api/v1/matching/match", json={
            "resume_id": resume["resume_id"], "job_id": job.json()["job_id"]
        })
        assert matched.status_code == 201, matched.text
        result = matched.json()
        assert "aws" in result["missing_skills"]
        assert 0 <= result["final_match_score"] <= 100
        monkeypatch.setattr("app.services.rag_service.create_query_embedding",
                            lambda text: [1.0] + [0.0] * 383)
        recommendations = client.get(
            f"/api/v1/rag/recommendations/{result['match_result_id']}"
        )
        assert recommendations.status_code == 200, recommendations.text
        for item in recommendations.json()["recommendations"]:
            assert all(chunk["skill"] == item["missing_skills"]
                       for chunk in item["retrieved_knowledge"])
    finally:
        (UPLOAD_DIR / resume["stored_filename"]).unlink(missing_ok=True)


def test_invalid_pdf_returns_400(client):
    response = client.post("/api/v1/resume/upload", files={
        "file": ("broken.pdf", b"not a pdf", "application/pdf")
    })
    assert response.status_code == 400


def test_vector_search_orders_and_filters(db):
    near = [1.0] + [0.0] * 383
    far = [0.0, 1.0] + [0.0] * 382
    db.add_all([
        KnowledgeChunk(skill="test-skill", title="Near", content="Near", embedding=near),
        KnowledgeChunk(skill="test-skill", title="Far", content="Far", embedding=far),
    ])
    db.flush()
    results = search_similar_chunks(db, near, skill="test-skill", top_k=2)
    assert [chunk.title for chunk in results] == ["Near", "Far"]
    assert len(search_similar_chunks(db, near, top_k=1)) == 1
    assert search_similar_chunks(db, near, skill="unknown-test-skill") == []


def test_skill_extraction_works_outside_project_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert "python" in extract_skills("Python developer")
