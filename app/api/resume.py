import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from app.services.resume_parser import extract_text_from_pdf
from app.services.text_cleaner import clean_text
from app.services.skill_extractor import extract_skills
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.resume import Resume

router = APIRouter()
UPLOAD_DIR = Path("uploads/resume")
UPLOAD_DIR.mkdir(parents=True, exist_ok = True)

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_resume(file: UploadFile = File(...), db:Session = Depends(get_db)):

    #1.validate filename
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File name is missing")

    #2. validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are allowed")

    max_bytes = 10 * 1024 * 1024
    file_content = await file.read(max_bytes + 1)
    if len(file_content) > max_bytes:
        raise HTTPException(status_code=413, detail="PDF must be 10 MB or smaller")
    if not file_content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= "Uploaded file is empty!")
    original_filename = file.filename or "resume.pdf"

    #3.Create unique filename
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"

    #4.Create file path
    file_path = UPLOAD_DIR / unique_filename

    #5.Save pdf
    file_path.write_bytes(file_content)

    #6.Extract text
    try:
        extracted_text = extract_text_from_pdf(file_path)
    except Exception as exc:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Unable to read PDF") from exc

    #7.Validate extracted text
    if not extracted_text.strip():
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not extract text form this pdf")

    #8.Clean text
    cleaned_text = clean_text(extracted_text)

    #9. Extract skills
    extracted_skills = extract_skills(cleaned_text)

    resume = Resume(
        original_filename=file.filename,
        stored_filename=unique_filename,
        content_type=file.content_type,
        extracted_text=extracted_text,
        cleaned_text=cleaned_text,
        extracted_skills=extracted_skills)

    try:
        db.add(resume)
        db.commit()
        db.refresh(resume)
    except Exception as exc:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Failed to save resume") from exc

    return {
        "Message": "Resume Uploaded Successfully",
        "resume_id": resume.id,
        "original_filename": file.filename,
        "stored_filename": unique_filename,
        "content_type": file.content_type,
        "extracted_text": extracted_text,
        "cleaned_text": cleaned_text,
        "extracted_skills": extracted_skills
    }
