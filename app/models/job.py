from datetime import datetime
from sqlalchemy import Text, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base

class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_description: Mapped[str] = mapped_column(Text, nullable=False)
    cleaned_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_skills : Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at : Mapped[datetime] = mapped_column(DateTime, default = datetime.utcnow)

