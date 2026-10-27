from datetime import datetime
from sqlalchemy import String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base

class Resume(Base):
    __tablename__ = "resumes"
    id : Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    original_filename : Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename : Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type : Mapped[str | None] = mapped_column(String(100), nullable=True)
    extracted_text : Mapped[str | None] = mapped_column( Text, nullable=True)
    cleaned_text : Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_skills : Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at : Mapped[datetime] = mapped_column(DateTime, default = datetime.utcnow)