from typing import Optional
from datetime import datetime, timezone
from sqlmodel import select
from .models import AccountingCredentialsModel
from shared.database import Database


class AccountingRepository:
    """Repository for accounting credentials database operations."""

    def __init__(self, db: Database):
        self.db = db

    def add_or_update_credentials(
        self,
        email: str,
        password: str,
        accounting_service_url: str,
        organization: Optional[str] = None,
    ) -> AccountingCredentialsModel:
        """Add or update accounting credentials."""
        with self.db.get_session() as session:
            # If credentials already exist, update them
            statement = select(AccountingCredentialsModel).where(
                AccountingCredentialsModel.email == email,
                AccountingCredentialsModel.accounting_service_url
                == accounting_service_url,
            )
            credentials = session.exec(statement).first()

            # If credentials are not found, create them
            if not credentials:
                # Check if any active credentials exist, if so mark them as inactive
                statement = (
                    select(AccountingCredentialsModel)
                    .where(AccountingCredentialsModel.active)
                    .update({"active": False})
                )
                session.exec(statement)

                # If no active credentials exist, set the new credentials as active
                credentials = AccountingCredentialsModel(
                    email=email,
                    password=password,
                    organization=organization,
                    accounting_service_url=accounting_service_url,
                    active=True,
                    created_at=datetime.now(timezone.utc),
                )
            else:
                # Update credentials
                credentials.password = password
                credentials.organization = (
                    organization if organization else credentials.organization
                )
                credentials.updated_at = datetime.now(timezone.utc)

            session.add(credentials)
            session.commit()
            session.refresh(credentials)
            return credentials

    def get_active_credentials(
        self, accounting_service_url: str
    ) -> Optional[AccountingCredentialsModel]:
        """Get active accounting credentials."""
        with self.db.get_session() as session:
            statement = select(AccountingCredentialsModel).where(
                AccountingCredentialsModel.active,
                AccountingCredentialsModel.accounting_service_url
                == accounting_service_url,
            )
            return session.exec(statement).first()

    def delete_credentials(self, email: str, accounting_service_url: str) -> bool:
        """Delete accounting credentials by email."""
        with self.db.get_session() as session:
            # Get credentials by email and accounting service url
            statement = select(AccountingCredentialsModel).where(
                AccountingCredentialsModel.email == email,
                AccountingCredentialsModel.accounting_service_url
                == accounting_service_url,
            )
            credentials = session.exec(statement).first()

            # If credentials are not found, return False
            if not credentials:
                return False

            # Delete credentials
            session.delete(credentials)
            session.commit()
            return True

    def get_credentials_by_email_and_url(
        self, email: str, accounting_service_url: str
    ) -> Optional[AccountingCredentialsModel]:
        """Get credentials by email and accounting service URL."""
        with self.db.get_session() as session:
            statement = select(AccountingCredentialsModel).where(
                AccountingCredentialsModel.email == email,
                AccountingCredentialsModel.accounting_service_url
                == accounting_service_url,
            )
            return session.exec(statement).first()

    def list_all_credentials(self) -> list[AccountingCredentialsModel]:
        """List all accounting credentials."""
        with self.db.get_session() as session:
            statement = select(AccountingCredentialsModel).order_by(
                AccountingCredentialsModel.created_at.desc()
            )
            return session.exec(statement).all()
