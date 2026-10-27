from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class DiscoverySettings(Base):
    __tablename__='discovery_settings'
    id:Mapped[int]=mapped_column(primary_key=True)
    sources:Mapped[list]=mapped_column(JSON,default=list)
