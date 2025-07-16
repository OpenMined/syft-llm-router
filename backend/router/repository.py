from typing import Optional, List
from sqlmodel import select
from .models import Router
from shared.database import BaseRepository, Database


class RouterRepository(BaseRepository):
    def __init__(self, db: Optional[Database] = None):
        super().__init__(db or Database())

    def get_router_by_name(
        self, name: str, published: Optional[bool] = None
    ) -> Optional[Router]:
        session = self.get_session()
        try:
            if published is not None:
                return session.exec(
                    select(Router).where(
                        Router.name == name, Router.published == published
                    )
                ).first()
            else:
                return session.exec(select(Router).where(Router.name == name)).first()
        finally:
            session.close()

    def get_all_routers(self) -> List[Router]:
        session = self.get_session()
        try:
            return session.exec(select(Router)).all()
        finally:
            session.close()

    def delete_router(self, name: str):
        session = self.get_session()
        try:
            router = session.exec(select(Router).where(Router.name == name)).first()
            if router:
                session.delete(router)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def get_routers_by_author(self, author: str, published: Optional[bool] = None):
        session = self.get_session()
        try:
            if published is not None:
                return session.exec(
                    select(Router).where(
                        Router.author == author, Router.published == published
                    )
                ).all()
            else:
                return session.exec(select(Router).where(Router.author == author)).all()
        finally:
            session.close()

    def add_or_update_router(self, router: Router):
        session = self.get_session()
        try:
            session.add(router)
            session.commit()
        finally:
            session.close()
