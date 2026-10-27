"""Single-user local job-search tracking, separate from matching data."""
from datetime import date, datetime
from sqlalchemy import Date, DateTime, ForeignKey, String, Text, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class Application(Base):
    __tablename__ = "applications"
    __table_args__=(Index('uq_application_source','source_key',unique=True),)
    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[int] = mapped_column(Integer,nullable=False,default=1,server_default='1')
    __mapper_args__={'version_id_col':version}
    match_result_id: Mapped[int | None] = mapped_column(ForeignKey("match_results.id"), unique=True, nullable=True)
    title: Mapped[str] = mapped_column(String(200))
    company: Mapped[str] = mapped_column(String(200), default="")
    url: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="saved")
    notes: Mapped[str] = mapped_column(Text, default="")
    job_description: Mapped[str] = mapped_column(Text, default="", server_default="")
    next_action: Mapped[str] = mapped_column(String(500), default="", server_default="")
    source_key: Mapped[str | None] = mapped_column(String(300),nullable=True)
    follow_up: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
