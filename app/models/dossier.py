"""An opportunity's correspondence, preparation, contacts, and submitted files."""
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, String, Text, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class CareerEvent(Base):
    __tablename__ = 'career_events'
    __table_args__=(Index('uq_career_event_source','application_id','source_key',unique=True),)
    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey('applications.id'), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, default='')
    source_key: Mapped[str | None] = mapped_column(String(250),nullable=True)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda:datetime.now(timezone.utc))


class CareerDocument(Base):
    __tablename__ = 'career_documents'
    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey('applications.id'), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    storage_name: Mapped[str] = mapped_column(String(100), unique=True)
    label: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda:datetime.now(timezone.utc))


class CareerContact(Base):
    __tablename__ = 'career_contacts'
    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey('applications.id'), index=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(300), default='')
    role: Mapped[str] = mapped_column(String(200), default='')
    notes: Mapped[str] = mapped_column(Text, default='')
