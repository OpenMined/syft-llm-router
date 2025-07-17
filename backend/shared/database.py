from pathlib import Path
from typing import Generator
from contextlib import contextmanager
from sqlmodel import SQLModel, Session, create_engine


class Database:
    def __init__(self, db_path: Path):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f"sqlite:///{db_path}")

    def create_db_and_tables(self):
        SQLModel.metadata.create_all(self.engine)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        with Session(self.engine) as session:
            yield session


# Optional: Base repository for shared CRUD logic
class BaseRepository:
    def __init__(self, db: Database):
        self.db = db
