"""User repository for authentication and dev session management."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User

DEFAULT_DEV_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_or_create_dev_user(self) -> User:
        """Ensures a default clinician user exists for development/testing."""
        result = await self.db.execute(select(User).where(User.id == DEFAULT_DEV_USER_ID))
        user = result.scalar_one_or_none()
        if user:
            return user

        user = User(
            id=DEFAULT_DEV_USER_ID,
            email="doctor@clinic.local",
            password_hash="argon2id_dev_placeholder_hash",
            display_name="Dr. Sarah Jenkins",
            role="clinician",
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
