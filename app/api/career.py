"""Personal job-search helpers. Intended for a local, single-user workspace."""
import re
import json
from pathlib import Path
from datetime import date, datetime, timezone, timedelta
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError
from app.database.session import get_db
from app.models.application import Application
from app.models.match_result import MatchResult
from app.models.resume import Resume
from app.models.preferences import SearchPreferences
from app.models.dossier import CareerEvent
from app.services.skill_extractor import extract_skills
from app.services.text_cleaner import clean_text

router = APIRouter()
PROFILE_PATH = Path(__file__).resolve().parents[2] / '.local' / 'career-profile.json'


@router.get('/profile')
def personal_profile():
    if not PROFILE_PATH.exists():
        return {'configured': False}
    data = json.loads(PROFILE_PATH.read_text(encoding='utf-8'))
    return {'configured': True, **data}


class ApplicationInput(BaseModel):
    application_id: int | None = Field(default=None, gt=0)
    version: int | None = Field(default=None,gt=0)
    match_result_id: int | None = Field(default=None, gt=0)
    title: str = Field(min_length=1, max_length=200)
    company: str = Field(default="", max_length=200)
    url: str = Field(default="", max_length=2000)
    status: Literal['saved', 'applied', 'interview', 'offer', 'closed'] = 'saved'
    notes: str = Field(default="", max_length=10000)
    job_description: str = Field(default="", max_length=50000)
    next_action: str = Field(default="", max_length=500)
    follow_up: date | None = None

    @field_validator('title')
    @classmethod
    def title_not_blank(cls, value):
        if not value.strip():
            raise ValueError('Enter a job title')
        return value.strip()

    @field_validator('url')
    @classmethod
    def safe_url(cls, value):
        if value and not re.match(r'^https?://[^\s]+$', value, re.I):
            raise ValueError('Use an http or https job link')
        return value


@router.get('/resumes')
def recent_resumes(db: Session = Depends(get_db)):
    return [{'id': r.id, 'filename': r.original_filename, 'skills': r.extracted_skills or []}
            for r in db.query(Resume).order_by(Resume.id.desc()).limit(20).all()]


@router.get('/review/{match_id}')
def resume_review(match_id: int, db: Session = Depends(get_db)):
    match = db.get(MatchResult, match_id)
    if not match:
        raise HTTPException(404, 'Comparison not found')
    resume = db.get(Resume, match.resume_id)
    # Only quote existing resume text; never invent experience or accomplishments.
    sentences = [s.strip() for s in re.split(r'[\n.!?]+', resume.extracted_text or '') if s.strip()]
    evidence = []
    for skill in match.matched_skills or []:
        snippets = [s[:400] for s in sentences if skill in extract_skills(clean_text(s))][:2]
        evidence.append({'skill': skill, 'snippets': snippets})
    return {
        'match_id': match_id,
        'evidence': evidence,
        'gaps': [{'skill': skill,
                  'action': f'Check whether you have real {skill} experience missing from this resume. '
                            'If yes, add a specific example. Otherwise, treat it as a learning gap.'}
                 for skill in match.missing_skills or []],
        'checklist': [
            'Move your most relevant project or experience near the top.',
            'For each matched skill, describe what you built, your contribution, and a measurable result you can verify.',
            'Read the full job description for experience, language, location, and work authorization requirements.',
            'Apply based on the full role and your interests; this overlap score is not a hiring prediction.'
        ],
        'bullet_template': 'Built [real project or feature] using [skill you used] to [purpose]; achieved [result you can substantiate].'
    }


@router.get('/applications')
def applications(db: Session = Depends(get_db)):
    rows = db.query(Application, MatchResult.final_match_score).outerjoin(
        MatchResult, Application.match_result_id == MatchResult.id
    ).order_by(Application.id.desc()).all()
    return [{**{key: getattr(row, key) for key in Application.__table__.columns.keys()},
             'score': score} for row, score in rows]


class DirectionInput(BaseModel):
    role: str = Field(default='', max_length=200)
    location: str = Field(default='', max_length=200)
    priorities: str = Field(default='', max_length=5000)


@router.get('/direction')
def get_direction(db: Session = Depends(get_db)):
    row = db.get(SearchPreferences, 1)
    return {key:getattr(row,key) if row else '' for key in ('role','location','priorities')}


@router.put('/direction')
def save_direction(data: DirectionInput, db: Session = Depends(get_db)):
    row = db.get(SearchPreferences, 1)
    if row is None:
        row = SearchPreferences(id=1)
        db.add(row)
    for key,value in data.model_dump().items():
        setattr(row,key,value.strip())
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(500, 'Could not save your search direction') from exc
    return {'saved':True}


@router.get('/today')
def today_overview(today: date | None = None, db: Session = Depends(get_db)):
    today = today or datetime.now(timezone(timedelta(hours=9))).date()
    rows = db.query(Application).all()
    active = [row for row in rows if row.status not in ('offer','closed')]
    due = sorted([row for row in active if row.follow_up and row.follow_up <= today],
                 key=lambda row:(row.follow_up,row.id))
    upcoming = sorted([row for row in active if row.follow_up and row.follow_up > today],
                      key=lambda row:(row.follow_up,row.id))[:5]
    def task(row):
        return {'id':row.id,'title':row.title,'company':row.company,
                'follow_up':row.follow_up,'next_action':row.next_action or 'Review this role and decide your next step',
                'status':row.status}
    scheduled=db.query(CareerEvent,Application).join(Application,Application.id==CareerEvent.application_id).filter(
        CareerEvent.done.is_(False),CareerEvent.scheduled_for.is_not(None),
        CareerEvent.scheduled_for < datetime.combine(today+timedelta(days=8),datetime.min.time(),tzinfo=timezone(timedelta(hours=9))),
        Application.status.notin_(['offer','closed'])
    ).order_by(CareerEvent.scheduled_for,CareerEvent.id).limit(20).all()
    return {'date':today,'counts':{state:sum(row.status==state for row in rows)
                                  for state in ('saved','applied','interview','offer','closed')},
            'due':[task(row) for row in due], 'upcoming':[task(row) for row in upcoming],
            'needs_next_action':[task(row) for row in active if not row.next_action][:5],
            'scheduled':[{'id':row.id,'title':f'{row.title}: {event.title}', 'company':row.company,
                          'next_action':event.body[:300] or event.kind,'scheduled_for':event.scheduled_for,
                          'status':row.status,'event_id':event.id} for event,row in scheduled]}


@router.put('/applications')
def save_application(data: ApplicationInput, db: Session = Depends(get_db)):
    if data.match_result_id and not db.get(MatchResult, data.match_result_id):
        raise HTTPException(404, 'Comparison not found')
    row = db.get(Application, data.application_id) if data.application_id else (
        db.query(Application).filter_by(match_result_id=data.match_result_id).first()
        if data.match_result_id else None
    )
    if data.application_id and row is None:
        raise HTTPException(404, 'Saved role not found')
    if row is not None and data.version is not None and row.version!=data.version:
        raise HTTPException(409,'This role changed since you opened it. Your edits were not saved. Reopen the role to review the latest version before merging your changes.')
    if row is None:
        row = Application()
        db.add(row)
        previous_status=None
    else:
        previous_status=row.status
    for key, value in data.model_dump(exclude={'application_id','version'}).items():
        setattr(row, key, value)
    try:
        db.flush()
        if previous_status!=row.status:
            db.add(CareerEvent(application_id=row.id,kind='status',
                title='Role saved' if previous_status is None else f'Status changed: {previous_status} → {row.status}',
                body=f'Current status: {row.status}',done=True))
        db.commit()
        db.refresh(row)
    except StaleDataError as exc:
        db.rollback()
        raise HTTPException(409,'This role was changed by another save. Your edits were not saved; review the latest version first.') from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(500, 'Could not save application') from exc
    return {'id': row.id, 'match_result_id': row.match_result_id,'version':row.version}
