from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class SearchPreferences(Base):
    __tablename__ = 'search_preferences'
    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str] = mapped_column(String(200), default='')
    location: Mapped[str] = mapped_column(String(200), default='')
    priorities: Mapped[str] = mapped_column(Text, default='')
