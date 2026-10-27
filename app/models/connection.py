from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class Connection(Base):
    __tablename__ = 'profile_connections'
    id: Mapped[int] = mapped_column(primary_key=True)
    github: Mapped[str] = mapped_column(String(39), default='')
    linkedin: Mapped[str] = mapped_column(String(300), default='')
