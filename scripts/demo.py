"""Run against the API: python scripts/demo.py [base_url]. Uses synthetic data."""
import json
import sys
import pymupdf as fitz
import httpx


def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Demo Candidate: Python, FastAPI, PostgreSQL and Docker developer")
    pdf = document.tobytes()
    document.close()
    with httpx.Client(base_url=base_url, timeout=180) as client:
        def request(method, path, **kwargs):
            response = client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()

        resume = request("POST", "/api/v1/resume/upload", files={
            "file": ("synthetic-resume.pdf", pdf, "application/pdf")
        })
        job = request("POST", "/api/v1/jobs/analyze", json={
            "job_description": "Python FastAPI PostgreSQL developer with Docker and AWS experience"
        })
        match = request("POST", "/api/v1/matching/match", json={
            "resume_id": resume["resume_id"], "job_id": job["job_id"]
        })
        recommendations = request("GET", f"/api/v1/rag/recommendations/{match['match_result_id']}")
        print(json.dumps({"match": match, "learning_plan": recommendations}, indent=2))


if __name__ == "__main__":
    main()
