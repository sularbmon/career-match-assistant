from fastapi import APIRouter, status, Depends, HTTPException
from app.schemas.job import JobAnalyzeRequest
from app.services.text_cleaner import clean_text
from app.services.skill_extractor import extract_skills
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.job import Job

router = APIRouter()

@router.post("/analyze", status_code=status.HTTP_201_CREATED)

async def analyze_job(data:JobAnalyzeRequest, db: Session = Depends(get_db)):
    "Analyze job description and extract required skills"

    #1. Validate request
    job_description = data.job_description

    #2. Clean text
    cleaned_text = clean_text(job_description)
    if not cleaned_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job Description is empty after cleaning")

    #3. Extract skills
    extracted_skills = extract_skills(cleaned_text)

    #4. Create job Database object
    job = Job(
        job_description = job_description,
        cleaned_text = cleaned_text,
        extracted_skills = extracted_skills
    )

    #5. Save to Postgresql
    try:
        db.add(job)
        db.commit()
        db.refresh(job)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to save job to database") from e

    #6. Return Response
    return {
        "message" : "Job analyzed successfully",
        "job_id" : job.id,
        "job_description" : job_description,
        "cleaned_text" : cleaned_text,
        "extracted_skills" : extracted_skills
    }
