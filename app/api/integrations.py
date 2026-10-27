"""Read-only, local personal-account helpers. No automatic tracker writes."""
import re
from pathlib import Path
import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from fastapi import Depends
from app.database.session import get_db
from app.models.connection import Connection
from app.models.dossier import CareerEvent
from app.api.dossier import require_application
from sqlalchemy.exc import IntegrityError

router = APIRouter()
LOCAL_DIR = Path(__file__).resolve().parents[2] / '.local'
GMAIL_SCOPE = 'https://www.googleapis.com/auth/gmail.readonly'


class GmailHeaderInput(BaseModel):
    application_id:int=Field(gt=0)
    message_id:str=Field(pattern=r'^[A-Za-z0-9_-]{1,200}$')
    subject:str=Field(min_length=1,max_length=2000)
    sender:str=Field(default='',max_length=1000)
    date:str=Field(default='',max_length=1000)


@router.post('/gmail/save-to-role')
def save_gmail_header(data:GmailHeaderInput,db:Session=Depends(get_db)):
    require_application(db,data.application_id)
    key=f'gmail:{data.message_id}'
    existing=db.query(CareerEvent).filter_by(application_id=data.application_id,source_key=key).first()
    if existing:return {'id':existing.id,'already_saved':True}
    row=CareerEvent(application_id=data.application_id,kind='email',title=data.subject[:200],
        body=f'Gmail header saved after user review.\nFrom: {data.sender}\nDate: {data.date}\nSubject: {data.subject}\nOpen: https://mail.google.com/mail/u/0/#all/{data.message_id}',
        done=True,source_key=key)
    db.add(row)
    try:db.commit();db.refresh(row)
    except IntegrityError:
        db.rollback()
        existing=db.query(CareerEvent).filter_by(application_id=data.application_id,source_key=key).first()
        if existing:return {'id':existing.id,'already_saved':True}
        raise HTTPException(500,'Could not save message reference')
    except Exception as exc:
        db.rollback();raise HTTPException(500,'Could not save message reference') from exc
    return {'id':row.id,'already_saved':False}


class ProfileLinks(BaseModel):
    github: str = Field(default='', max_length=39)
    linkedin: str = Field(default='', max_length=300)

    @field_validator('github')
    @classmethod
    def github_username(cls, value):
        if value and not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?', value):
            raise ValueError('Enter a GitHub username, not a URL')
        return value

    @field_validator('linkedin')
    @classmethod
    def linkedin_url(cls, value):
        if value and not re.fullmatch(r'https://(?:www\.)?linkedin\.com/in/[A-Za-z0-9_%\-]+/?', value):
            raise ValueError('Enter an https://www.linkedin.com/in/... profile link')
        return value


@router.get('/status')
def status(db: Session = Depends(get_db)):
    row = db.get(Connection, 1)
    return {'github': row.github if row else '', 'linkedin': row.linkedin if row else '',
            'gmail': 'authorization-file-present' if (LOCAL_DIR/'gmail-token.json').exists() else 'setup-required',
            'github_mode': 'public-preview', 'linkedin_mode': 'profile-link-only'}


@router.put('/profiles')
def save_profiles(data: ProfileLinks, db: Session = Depends(get_db)):
    row = db.get(Connection, 1)
    if row is None:
        row = Connection(id=1)
        db.add(row)
    row.github, row.linkedin = data.github, data.linkedin
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(500, 'Could not save profile links') from exc
    return {'saved': True}


@router.get('/github/{username}')
def github_preview(username: str):
    try:
        ProfileLinks(github=username)
    except ValueError as exc:
        raise HTTPException(422, 'Invalid GitHub username') from exc
    try:
        with httpx.Client(timeout=15, follow_redirects=False,
                          headers={'Accept':'application/vnd.github+json', 'User-Agent':'CareerMatch-Local'}) as client:
            profile = client.get(f'https://api.github.com/users/{username}')
            repos = client.get(f'https://api.github.com/users/{username}/repos',
                               params={'per_page':100, 'sort':'updated', 'type':'owner'})
        if profile.status_code == 404:
            raise HTTPException(404, 'GitHub user not found')
        if 403 in (profile.status_code, repos.status_code) or 429 in (profile.status_code, repos.status_code):
            raise HTTPException(429, 'GitHub public API rate limit reached. Try later.')
        profile.raise_for_status(); repos.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(502, 'GitHub could not be reached. Try later.') from exc
    user = profile.json()
    projects = [{'name': r['name'], 'url': r['html_url'], 'description': r.get('description') or '',
                 'language': r.get('language'), 'topics': r.get('topics') or [], 'fork':r['fork']}
                for r in repos.json() if not r.get('archived')]
    return {'username':user['login'], 'name':user.get('name'), 'bio':user.get('bio'),
            'projects':projects, 'limit_note':'Up to 100 recently updated repositories; archived repositories excluded. '
            'Public metadata is evidence to review, not proof of authorship or proficiency.'}


@router.get('/gmail/messages')
def gmail_messages(query: str = Query(default='label:job-search newer_than:90d', min_length=1, max_length=500)):
    path = LOCAL_DIR / 'gmail-token.json'
    if not path.exists():
        raise HTTPException(409, 'Authorize Gmail locally first. See docs/INTEGRATIONS.md.')
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import AuthorizedSession
    except ImportError as exc:
        raise HTTPException(503, 'Install requirements-integrations.txt first.') from exc
    try:
        credentials = Credentials.from_authorized_user_file(str(path), scopes=[GMAIL_SCOPE])
        with AuthorizedSession(credentials) as session:
            response = session.get('https://gmail.googleapis.com/gmail/v1/users/me/messages',
                                   params={'q':query, 'maxResults':20}, timeout=15)
            response.raise_for_status()
            messages = []
            for ref in response.json().get('messages', []):
                detail = session.get(f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{ref['id']}",
                                     params={'format':'metadata'}, timeout=15)
                detail.raise_for_status()
                message = detail.json()
                headers = {h['name'].lower():h['value'] for h in message.get('payload', {}).get('headers', [])}
                messages.append({'id':message['id'], 'subject':headers.get('subject','(No subject)'),
                                 'sender':headers.get('from',''), 'date':headers.get('date',''),
                                 'url':f"https://mail.google.com/mail/u/0/#all/{message['id']}"})
        # Refreshes can update the access token. Keep it local and out of API responses.
        path.write_text(credentials.to_json(), encoding='utf-8')
        return {'messages':messages, 'limit':20, 'query':query}
    except Exception as exc:
        raise HTTPException(502, 'Gmail access failed. Check authorization or reconnect using the local script.') from exc
