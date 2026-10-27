import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.application import Application
from app.models.match_result import MatchResult
from app.models.job import Job
from app.models.resume import Resume
from app.models.preferences import SearchPreferences
from app.api.career import PROFILE_PATH
from app.services.career_assistant import build_review

router=APIRouter()


@router.get('/applications/{application_id}/assistant')
def opportunity_assistant(application_id:int,resume_id:int|None=Query(default=None,gt=0),db:Session=Depends(get_db)):
    application=db.get(Application,application_id)
    if application is None:raise HTTPException(404,'Saved role not found')
    match=db.get(MatchResult,application.match_result_id) if application.match_result_id else None
    if resume_id is None and match:resume_id=match.resume_id
    if resume_id is None and PROFILE_PATH.exists():
        try:resume_id=json.loads(PROFILE_PATH.read_text(encoding='utf-8')).get('resume_id')
        except (OSError,ValueError):pass
    resume=db.get(Resume,resume_id) if resume_id else None
    if resume_id and resume is None:raise HTTPException(404,'Selected CV not found; choose another version')
    description=application.job_description or ''
    if not description and match:
        job=db.get(Job,match.job_id)
        description=job.job_description if job else ''
    direction=db.get(SearchPreferences,1)
    preferences={key:getattr(direction,key) if direction else '' for key in ('role','location','priorities')}
    return build_review(application,resume,description,preferences)
