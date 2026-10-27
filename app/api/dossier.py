from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.application import Application
from app.models.dossier import CareerEvent, CareerDocument, CareerContact

router = APIRouter()
DOCUMENT_DIR = Path(__file__).resolve().parents[2] / 'uploads' / 'career'
ALLOWED_EXTENSIONS = {'.pdf','.docx','.txt','.md','.png','.jpg','.jpeg','.eml','.ics'}


def require_application(db, application_id):
    if db.get(Application, application_id) is None:
        raise HTTPException(404, 'Saved role not found')


def save(db):
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(500, 'Could not save this item') from exc


def fields(row):
    return {column.name:getattr(row,column.name) for column in row.__table__.columns
            if column.name != 'storage_name'}


class EventInput(BaseModel):
    kind: Literal['note','task','interview','email'] = 'note'
    title: str = Field(min_length=1,max_length=200)
    body: str = Field(default='',max_length=20000)
    scheduled_for: datetime | None = None
    done: bool = False

    @field_validator('title')
    @classmethod
    def meaningful_title(cls,value):
        if not value.strip(): raise ValueError('Enter a title')
        return value.strip()

    @field_validator('scheduled_for')
    @classmethod
    def timezone_required(cls,value):
        if value is not None and value.utcoffset() is None:
            raise ValueError('Include a timezone for scheduled items')
        return value


class ContactInput(BaseModel):
    name: str = Field(min_length=1,max_length=200)
    email: str = Field(default='',max_length=300)
    role: str = Field(default='',max_length=200)
    notes: str = Field(default='',max_length=10000)

    @field_validator('name')
    @classmethod
    def meaningful_name(cls,value):
        if not value.strip(): raise ValueError('Enter a name')
        return value.strip()


@router.get('/applications/{application_id}/dossier')
def dossier(application_id:int,db:Session=Depends(get_db)):
    require_application(db,application_id)
    events=db.query(CareerEvent).filter_by(application_id=application_id).order_by(CareerEvent.created_at.desc(),CareerEvent.id.desc()).all()
    documents=db.query(CareerDocument).filter_by(application_id=application_id).order_by(CareerDocument.id.desc()).all()
    contacts=db.query(CareerContact).filter_by(application_id=application_id).order_by(CareerContact.id).all()
    return {'events':[fields(row) for row in events], 'documents':[fields(row) for row in documents],
            'contacts':[fields(row) for row in contacts]}


@router.post('/applications/{application_id}/events',status_code=201)
def add_event(application_id:int,data:EventInput,db:Session=Depends(get_db)):
    require_application(db,application_id)
    row=CareerEvent(application_id=application_id,**data.model_dump())
    db.add(row);save(db);db.refresh(row)
    return fields(row)


@router.put('/applications/{application_id}/events/{event_id}')
def update_event(application_id:int,event_id:int,data:EventInput,db:Session=Depends(get_db)):
    row=db.get(CareerEvent,event_id)
    if row is None or row.application_id != application_id:
        raise HTTPException(404,'Timeline item not found for this role')
    for key,value in data.model_dump().items():setattr(row,key,value)
    save(db)
    return fields(row)


@router.post('/applications/{application_id}/contacts',status_code=201)
def add_contact(application_id:int,data:ContactInput,db:Session=Depends(get_db)):
    require_application(db,application_id)
    row=CareerContact(application_id=application_id,**data.model_dump())
    db.add(row);save(db);db.refresh(row)
    return fields(row)


@router.post('/applications/{application_id}/documents',status_code=201)
async def upload_document(application_id:int,file:UploadFile=File(...),label:str=Form(default=''),db:Session=Depends(get_db)):
    require_application(db,application_id)
    filename=Path((file.filename or '').replace('\\','/')).name
    extension=Path(filename).suffix.lower()
    if not filename or extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(400,'Use PDF, DOCX, TXT, MD, image, EML, or ICS files')
    if len(filename)>255 or len(label)>200:
        raise HTTPException(422,'Filename or document label is too long')
    data=await file.read(10*1024*1024+1)
    if not data:raise HTTPException(400,'File is empty')
    if len(data)>10*1024*1024:raise HTTPException(413,'File must be 10 MB or smaller')
    DOCUMENT_DIR.mkdir(parents=True,exist_ok=True)
    storage_name=f'{uuid4()}{extension}'
    path=DOCUMENT_DIR/storage_name
    path.write_bytes(data)
    row=CareerDocument(application_id=application_id,filename=filename,storage_name=storage_name,label=label.strip() or filename[:200])
    try:
        db.add(row);save(db);db.refresh(row)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return fields(row)


@router.get('/applications/{application_id}/documents/{document_id}')
def download_document(application_id:int,document_id:int,db:Session=Depends(get_db)):
    row=db.get(CareerDocument,document_id)
    if row is None or row.application_id!=application_id:
        raise HTTPException(404,'Document not found for this role')
    path=(DOCUMENT_DIR/row.storage_name).resolve()
    if not path.is_relative_to(DOCUMENT_DIR.resolve()) or not path.is_file():
        raise HTTPException(404,'Stored file is unavailable')
    return FileResponse(path,filename=row.filename,media_type='application/octet-stream',content_disposition_type='attachment')
