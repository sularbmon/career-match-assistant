from typing import Literal
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field,field_validator
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database.session import get_db
from app.models.discovery import DiscoverySettings
from app.models.application import Application
from app.models.dossier import CareerEvent
from app.services import job_discovery

router=APIRouter()
DEFAULT_SOURCES=[{'provider':'lever','board':'woven-by-toyota','name':'Woven by Toyota'}]


class SourceInput(BaseModel):
    provider:Literal['lever','greenhouse']
    board:str=Field(pattern=r'^[A-Za-z0-9_-]{1,100}$')
    name:str=Field(min_length=1,max_length=200)

    @field_validator('name')
    @classmethod
    def nonempty_name(cls,value):
        if not value.strip():raise ValueError('Enter a company name')
        return value.strip()


class SourcesInput(BaseModel):
    sources:list[SourceInput]=Field(max_length=5)


class SearchInput(BaseModel):
    keywords:str=Field(default='',max_length=200)
    location:str=Field(default='',max_length=200)


class SavePostingInput(BaseModel):
    source:SourceInput
    posting_id:str=Field(pattern=r'^[A-Za-z0-9_-]{1,160}$')


def sources_for(db):
    row=db.get(DiscoverySettings,1)
    return row.sources if row else DEFAULT_SOURCES


@router.get('/sources')
def sources(db:Session=Depends(get_db)):
    return {'sources':sources_for(db),'example_default':db.get(DiscoverySettings,1) is None}


@router.put('/sources')
def save_sources(data:SourcesInput,db:Session=Depends(get_db)):
    if len({(row.provider,row.board.lower()) for row in data.sources})!=len(data.sources):
        raise HTTPException(422,'Each provider/board may appear only once')
    row=db.get(DiscoverySettings,1)
    if row is None:row=DiscoverySettings(id=1);db.add(row)
    row.sources=[source.model_dump() for source in data.sources]
    try:db.commit()
    except Exception as exc:db.rollback();raise HTTPException(500,'Could not save job sources') from exc
    return {'saved':True}


@router.post('/search')
def search(data:SearchInput,db:Session=Depends(get_db)):
    source_list=sources_for(db)
    if not source_list:raise HTTPException(409,'Add at least one company job board first')
    return job_discovery.search_sources(source_list,data.keywords.strip(),data.location.strip())


@router.post('/save')
def save_posting(data:SavePostingInput,db:Session=Depends(get_db)):
    key=f'{data.source.provider}:{data.source.board}:{data.posting_id}'
    existing=db.query(Application).filter_by(source_key=key).first()
    if existing:return {'id':existing.id,'already_saved':True}
    try:jobs,_=job_discovery.fetch_board(data.source.model_dump())
    except Exception as exc:raise HTTPException(502,'Could not verify the live posting. Try later or save it manually.') from exc
    job=next((job for job in jobs if job['id']==data.posting_id),None)
    if job is None:raise HTTPException(404,'Posting no longer found in the checked source. It may have closed.')
    existing=db.query(Application).filter_by(url=job['url']).first()
    if existing:
        existing.source_key=key
        try:db.commit()
        except Exception as exc:db.rollback();raise HTTPException(500,'Could not link this saved source') from exc
        return {'id':existing.id,'already_saved':True}
    description=f"Location: {job['location']}\nWork style: {job['workplace']}\n\n{job['description']}"
    row=Application(title=job['title'][:200],company=job['company'],url=job['url'],status='saved',
                    job_description=description[:50000],next_action='Review the posting and clarify requirements before deciding to apply.',source_key=key)
    try:
        db.add(row);db.flush()
        db.add(CareerEvent(application_id=row.id,kind='status',title='Live posting saved',
            body=f"Imported from {data.source.provider}/{data.source.board}. This is a snapshot; check the original posting before applying.\n{job['url']}",done=True))
        db.commit();db.refresh(row)
    except IntegrityError:
        db.rollback();existing=db.query(Application).filter_by(source_key=key).first()
        if existing:return {'id':existing.id,'already_saved':True}
        raise HTTPException(500,'Could not save posting')
    except Exception as exc:db.rollback();raise HTTPException(500,'Could not save posting') from exc
    return {'id':row.id,'already_saved':False}
