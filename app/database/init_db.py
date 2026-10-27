"""Initialize a new local/demo database: python -m app.database.init_db."""
from sqlalchemy import text
from app.database.base import Base
from app.database.session import engine
import app.models  # Register all tables with SQLAlchemy metadata.


def init_db():
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(bind=connection)
        # Compatibility update for local workspaces created before standalone tracking.
        connection.execute(text("ALTER TABLE applications ALTER COLUMN match_result_id DROP NOT NULL"))
        connection.execute(text("ALTER TABLE applications ADD COLUMN IF NOT EXISTS job_description TEXT NOT NULL DEFAULT ''"))
        connection.execute(text("ALTER TABLE applications ADD COLUMN IF NOT EXISTS next_action VARCHAR(500) NOT NULL DEFAULT ''"))
        connection.execute(text("ALTER TABLE career_events ADD COLUMN IF NOT EXISTS source_key VARCHAR(250)"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_career_event_source ON career_events (application_id, source_key)"))
        connection.execute(text("ALTER TABLE applications ADD COLUMN IF NOT EXISTS source_key VARCHAR(300)"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_application_source ON applications (source_key)"))
        connection.execute(text("ALTER TABLE applications ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1"))
    print("Database initialized.")


if __name__ == "__main__":
    init_db()
