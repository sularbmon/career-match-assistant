from fastapi import FastAPI
from app.api.router import api_router
from pathlib import Path
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="AI Job Match Platform",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"Message" : "AI Job Match Platform is Running...."}

@app.get("/health")
def health_check():
    return {"status" : "Healthy"}

app.include_router(api_router, prefix="/api/v1")

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/dashboard", include_in_schema=False)
def dashboard():
    return FileResponse(STATIC_DIR / "index.html")


@app.get('/integration-guide', include_in_schema=False)
def integration_guide():
    return FileResponse(STATIC_DIR.parent.parent / 'docs' / 'INTEGRATIONS.md', media_type='text/plain')


@app.get("/demo/resume.pdf", include_in_schema=False)
def demo_resume():
    import pymupdf
    with pymupdf.open() as document:
        page = document.new_page()
        page.insert_text((72, 72), "Synthetic Demo Candidate", fontsize=18)
        page.insert_text((72, 110), "Python, FastAPI, PostgreSQL and Docker developer.")
        page.insert_text((72, 135), "Built REST API services and tested backend applications.")
        return Response(document.tobytes(), media_type="application/pdf")
