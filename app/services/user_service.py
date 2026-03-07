"""Service layer for user CRUD operations."""
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from loguru import logger

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """Centralizes all user database operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID. Returns None if not found."""
        return self.db.query(User).filter(User.id == uuid.UUID(user_id)).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email. Returns None if not found."""
        return self.db.query(User).filter(User.email == email).first()

    def get_all(self, limit: int = 50, offset: int = 0) -> List[User]:
        """Get all users with pagination."""
        return self.db.query(User).offset(offset).limit(limit).all()

    def create(self, user_data: UserCreate) -> User:
        """Create and persist a new user. Raises ValueError if email already exists."""
        if self.get_by_email(user_data.email):
            raise ValueError(f"User with email {user_data.email} already exists")

        new_user = User(
            id=uuid.uuid4(),
            email=user_data.email,
            full_name=user_data.full_name,
            phone=user_data.phone,
            linkedin_url=user_data.linkedin_url,
            github_url=user_data.github_url,
            professional_summary=user_data.professional_summary,
            is_active=True,
        )

        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)

        logger.info(f"User created: {new_user.id}")
        return new_user

    def update(self, user_id: str, update_data: UserUpdate) -> Optional[User]:
        """Update a user's fields. Returns None if not found."""
        user = self.get_by_id(user_id)
        if not user:
            return None

        for key, value in update_data.dict(exclude_unset=True).items():
            setattr(user, key, value)

        self.db.commit()
        self.db.refresh(user)

        logger.info(f"User updated: {user_id}")
        return user

    def delete(self, user_id: str) -> bool:
        """Delete a user. Returns False if not found."""
        user = self.get_by_id(user_id)
        if not user:
            return False

        self.db.delete(user)
        self.db.commit()

        logger.info(f"User deleted: {user_id}")
        return True

    def to_dict(self, user: User) -> dict:
        """Convert a User ORM object to a plain dict for use in services."""
        return {
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "linkedin_url": user.linkedin_url,
            "github_url": user.github_url,
            "professional_summary": user.professional_summary,
        }
