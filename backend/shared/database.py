from pathlib import Path
from typing import Generator
from sqlmodel import SQLModel, Session, create_engine


class Database:
    def __init__(self, db_path: Path):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f"sqlite:///{db_path}")

    def create_db_and_tables(self):
        SQLModel.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        return Session(self.engine)


# Optional: Base repository for shared CRUD logic
class BaseRepository:
    def __init__(self, db: Database):
        self.db = db
        self.engine = db.engine

    def get_session(self) -> Session:
        return self.db.get_session()
