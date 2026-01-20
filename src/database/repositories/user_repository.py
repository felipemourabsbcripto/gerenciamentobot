"""
Repository for User model database operations.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User


class UserRepository:
    """Repository for User database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, telegram_id: int, username: str = None,
                     first_name: str = None, last_name: str = None) -> User:
        """Create a new user."""
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, telegram_id: int, username: str = None,
                            first_name: str = None, last_name: str = None) -> User:
        """Get existing user or create new one."""
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            user = await self.create(telegram_id, username, first_name, last_name)
        return user

    async def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user fields."""
        user = await self.get_by_id(user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            await self.session.flush()
        return user

    async def toggle_notifications(self, telegram_id: int) -> Optional[User]:
        """Toggle user notifications."""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.notifications_enabled = not user.notifications_enabled
            await self.session.flush()
        return user

    async def toggle_death_cross_alerts(self, telegram_id: int) -> Optional[User]:
        """Toggle death cross alerts."""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.death_cross_alerts = not user.death_cross_alerts
            await self.session.flush()
        return user

    async def update_reserve(self, telegram_id: int, reserve_amount: float) -> Optional[User]:
        """Update user's USDT reserve."""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.usdt_reserve = reserve_amount
            await self.session.flush()
        return user

    async def update_reserve_target(self, telegram_id: int, target_percent: float) -> Optional[User]:
        """Update user's reserve target percentage."""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.reserve_target_percent = target_percent
            await self.session.flush()
        return user

    async def get_all_users(self) -> List[User]:
        """Get all active users."""
        result = await self.session.execute(
            select(User).where(User.is_active == True)
        )
        return list(result.scalars().all())

    async def get_users_with_notifications(self) -> List[User]:
        """Get all active users with notifications enabled."""
        result = await self.session.execute(
            select(User).where(
                User.is_active == True,
                User.notifications_enabled == True
            )
        )
        return list(result.scalars().all())

    async def get_users_with_death_cross_alerts(self) -> List[User]:
        """Get all users with death cross alerts enabled."""
        result = await self.session.execute(
            select(User).where(
                User.is_active == True,
                User.death_cross_alerts == True
            )
        )
        return list(result.scalars().all())

    async def toggle_price_alerts(self, telegram_id: int) -> Optional[User]:
        """Toggle price alerts for user's assets."""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.price_alerts_enabled = not user.price_alerts_enabled
            await self.session.flush()
        return user

    async def update_check_interval(self, telegram_id: int, interval_minutes: int) -> Optional[User]:
        """Update price check interval for user."""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.check_interval_minutes = interval_minutes
            await self.session.flush()
        return user

    async def get_users_with_price_alerts(self) -> List[User]:
        """Get all users with price alerts enabled."""
        result = await self.session.execute(
            select(User).where(
                User.is_active == True,
                User.price_alerts_enabled == True
            )
        )
        return list(result.scalars().all())

    async def complete_registration(
        self,
        telegram_id: int,
        full_name: str,
        phone: str,
        birth_date: str,
        futures_balance: float = 0.0
    ) -> Optional[User]:
        """Complete user registration with required info."""
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            return None
        
        # Get next registration number
        result = await self.session.execute(
            select(func.max(User.registration_number))
        )
        max_num = result.scalar() or 0
        
        user.full_name = full_name
        user.phone = phone
        user.birth_date = birth_date
        user.futures_balance = futures_balance
        user.is_registered = True
        user.registration_number = max_num + 1
        
        await self.session.flush()
        return user

    async def accept_terms(self, telegram_id: int) -> Optional[User]:
        """Mark user as having accepted terms."""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.accepted_terms = True
            user.accepted_terms_at = datetime.utcnow()
            await self.session.flush()
        return user

    async def update_futures_balance(self, telegram_id: int, balance: float) -> Optional[User]:
        """Update user's futures balance."""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.futures_balance = balance
            await self.session.flush()
        return user

    async def add_to_futures_balance(self, telegram_id: int, amount: float) -> Optional[User]:
        """Add amount to user's futures balance."""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.futures_balance = (user.futures_balance or 0) + amount
            await self.session.flush()
        return user

    async def update_futures_risk_percent(self, telegram_id: int, risk_percent: float) -> Optional[User]:
        """Update user's futures risk percent per trade."""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            # Limitar entre 0.5% e 20%
            risk_percent = max(0.5, min(20.0, risk_percent))
            user.futures_risk_percent = risk_percent
            await self.session.flush()
        return user

    async def get_futures_risk_percent(self, telegram_id: int) -> float:
        """Get user's configured futures risk percent."""
        user = await self.get_by_telegram_id(telegram_id)
        if user and user.futures_risk_percent:
            return user.futures_risk_percent
        return 5.0  # Default 5%

    async def is_user_banned(self, telegram_id: int) -> bool:
        """Check if user is banned."""
        user = await self.get_by_telegram_id(telegram_id)
        return user.is_banned if user else False

    async def is_user_registered(self, telegram_id: int) -> bool:
        """Check if user is fully registered."""
        user = await self.get_by_telegram_id(telegram_id)
        return user.is_registered if user else False

