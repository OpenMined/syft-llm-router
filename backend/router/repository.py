from typing import Optional, List
from sqlmodel import select
from .models import RouterModel, RouterServiceModel, RouterMetadataModel
from .schemas import Router, RouterCreate, RouterUpdate
from shared.database import BaseRepository


class RouterRepository(BaseRepository):
    def get_router_by_name(
        self, name: str, published: Optional[bool] = None
    ) -> Optional[Router]:
        with self.db.get_session() as session:
            if published is not None:
                router = session.exec(
                    select(RouterModel).where(
                        RouterModel.name == name, RouterModel.published == published
                    )
                ).first()
            else:
                router = session.exec(
                    select(RouterModel).where(RouterModel.name == name)
                ).first()

            return Router.model_validate(router) if router else None

    def get_all_routers(self) -> List[Router]:
        with self.db.get_session() as session:
            routers = session.exec(select(RouterModel)).all()

            return [Router.model_validate(router) for router in routers]

    def delete_router(self, name: str) -> bool:
        with self.db.get_session() as session:
            router = session.exec(
                select(RouterModel).where(RouterModel.name == name)
            ).first()
            if router:
                session.delete(router)
                session.commit()
                return True
        return False

    def get_routers_by_author(
        self, author: str, published: Optional[bool] = None
    ) -> List[Router]:
        with self.db.get_session() as session:
            if published is not None:
                routers = session.exec(
                    select(RouterModel).where(
                        RouterModel.author == author, RouterModel.published == published
                    )
                ).all()
            else:
                routers = session.exec(
                    select(RouterModel).where(RouterModel.author == author)
                ).all()

            return [Router.model_validate(router) for router in routers]

    def create_or_update_router(
        self, router_name: str, router_update: RouterUpdate
    ) -> Optional[Router]:
        """Create or update router metadata and services (router itself always exists)"""
        with self.db.get_session() as session:
            router_orm = session.exec(
                select(RouterModel).where(RouterModel.name == router_name)
            ).first()

            if not router_orm:
                return None

            # Update basic fields if provided
            if router_update.published is not None:
                router_orm.published = router_update.published

            # Handle metadata: create if doesn't exist, update if exists
            if router_update.router_metadata is not None:
                if router_orm.router_metadata is None:
                    # Create new metadata
                    router_orm.router_metadata = RouterMetadataModel(
                        summary=router_update.router_metadata.summary,
                        description=router_update.router_metadata.description,
                        tags=router_update.router_metadata.tags,
                        code_hash=router_update.router_metadata.code_hash,
                        router_id=router_orm.id,
                    )
                else:
                    # Update existing metadata
                    router_orm.router_metadata.summary = (
                        router_update.router_metadata.summary
                    )
                    router_orm.router_metadata.description = (
                        router_update.router_metadata.description
                    )
                    router_orm.router_metadata.tags = router_update.router_metadata.tags
                    router_orm.router_metadata.code_hash = (
                        router_update.router_metadata.code_hash
                    )

            # Handle services: create if doesn't exist, update if exists
            if router_update.services is not None:
                # Create a map of existing services by type for easy lookup
                existing_services = {
                    service.type: service for service in router_orm.services
                }

                updated_services = []
                for service_dto in router_update.services:
                    if service_dto.type in existing_services:
                        # Update existing service
                        existing_service = existing_services[service_dto.type]
                        existing_service.enabled = service_dto.enabled
                        existing_service.pricing = service_dto.pricing
                        existing_service.charge_type = service_dto.charge_type
                        updated_services.append(existing_service)
                    else:
                        # Create new service
                        new_service = RouterServiceModel(
                            type=service_dto.type,
                            enabled=service_dto.enabled,
                            pricing=service_dto.pricing,
                            charge_type=service_dto.charge_type,
                            router_id=router_orm.id,
                        )
                        updated_services.append(new_service)

                router_orm.services = updated_services

            session.add(router_orm)
            session.commit()
            session.refresh(router_orm)

            return Router.model_validate(router_orm)

    def create_router(self, router_data: RouterCreate) -> Router:
        """Create a new router from Pydantic DTO"""
        with self.db.get_session() as session:
            # Convert Pydantic DTOs to ORM models
            services = [
                RouterServiceModel(
                    type=service.type,
                    enabled=service.enabled,
                    pricing=service.pricing,
                    charge_type=service.charge_type,
                )
                for service in router_data.services
            ]

            router_orm = RouterModel(
                name=router_data.name,
                router_type=router_data.router_type,
                author=router_data.author,
                published=router_data.published,
                services=services,
            )

            session.add(router_orm)
            session.commit()
            session.refresh(router_orm)

            # Return Pydantic DTO
            return Router.model_validate(router_orm)

    def set_published_status(
        self, router_name: str, published: bool
    ) -> Optional[Router]:
        with self.db.get_session() as session:
            router_orm = session.exec(
                select(RouterModel).where(RouterModel.name == router_name)
            ).first()

            if not router_orm:
                return None

            router_orm.published = published

            session.add(router_orm)
            session.commit()
            session.refresh(router_orm)

            return Router.model_validate(router_orm)
