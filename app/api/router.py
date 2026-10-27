from fastapi import APIRouter
from app.api import career
from app.api import integrations
from app.api import dossier
from app.api import backup
from app.api import assistant
from app.api import discovery
from app.api import (resume, jobs, matching, similarity, scoring, database, rag)

api_router = APIRouter()
api_router.include_router(career.router, prefix="/career", tags=["Job search"])
api_router.include_router(dossier.router, prefix="/career", tags=["Opportunity history"])
api_router.include_router(backup.router, prefix="/career", tags=["Workspace backup"])
api_router.include_router(assistant.router, prefix="/career", tags=["Personal assistant"])
api_router.include_router(discovery.router, prefix="/discovery", tags=["Job discovery"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["Account integrations"])

api_router.include_router(resume.router, prefix="/resume", tags=["Resume"])

api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])

api_router.include_router(matching.router, prefix="/matching", tags=["Matching"])

api_router.include_router(similarity.router, prefix="/similarity", tags=["Similarity"])

api_router.include_router(scoring.router, prefix="/scoring", tags=["Scoring"])

api_router.include_router(database.router, prefix="/database", tags=["Database"])

api_router.include_router(rag.router, prefix="/rag", tags=["RAG"])
