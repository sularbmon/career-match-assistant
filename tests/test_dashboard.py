from fastapi.testclient import TestClient
import pymupdf
from app.main import app


def test_dashboard_and_assets_are_served():
    with TestClient(app) as client:
        page = client.get('/dashboard')
        assert page.status_code == 200
        assert 'Compare with this role' in page.text
        assert client.get('/static/app.js').status_code == 200
        assert client.get('/static/style.css').status_code == 200


def test_sample_resume_is_a_readable_synthetic_pdf():
    with TestClient(app) as client:
        response = client.get('/demo/resume.pdf')
        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/pdf'
        with pymupdf.open(stream=response.content, filetype='pdf') as document:
            text = document[0].get_text()
        assert 'Synthetic Demo Candidate' in text
        assert 'FastAPI' in text
