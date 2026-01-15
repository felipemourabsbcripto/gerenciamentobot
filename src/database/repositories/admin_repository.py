"""
Repository for Admin operations.
"""
from datetime import datetime
from typing import Optional, List
import secrets
from sqlalchemy import select, update as sql_update, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User, InviteCode, AdminLog


# Admins mestres (apenas estes podem adicionar outros admins)
MASTER_ADMINS = ["ronaldo_fh", "gornicapital"]


class AdminRepository:
    """Repository for admin operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def is_master_admin(self, username: str) -> bool:
        """Check if username is a master admin."""
        return username and username.lower() in [a.lower() for a in MASTER_ADMINS]

    async def is_admin(self, telegram_id: int) -> bool:
        """Check if user is an admin."""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return False
        
        # Master admins are always admins
        if self.is_master_admin(user.username):
            return True
        
        return user.is_admin

    async def get_all_users(self, include_banned: bool = False) -> List[User]:
        """Get all registered users."""
        query = select(User).where(User.is_registered == True)
        if not include_banned:
            query = query.where(User.is_banned == False)
        query = query.order_by(User.registration_number)
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_user_stats(self) -> dict:
        """Get user statistics."""
        # Total registered
        total_result = await self.session.execute(
            select(func.count()).select_from(User).where(User.is_registered == True)
        )
        total = total_result.scalar() or 0
        
        # Active users
        active_result = await self.session.execute(
            select(func.count()).select_from(User).where(
                User.is_registered == True,
                User.is_banned == False,
                User.is_active == True
            )
        )
        active = active_result.scalar() or 0
        
        # Banned users
        banned_result = await self.session.execute(
            select(func.count()).select_from(User).where(User.is_banned == True)
        )
        banned = banned_result.scalar() or 0
        
        # Admins
        admin_result = await self.session.execute(
            select(func.count()).select_from(User).where(User.is_admin == True)
        )
        admins = admin_result.scalar() or 0
        
        return {
            "total": total,
            "active": active,
            "banned": banned,
            "admins": admins
        }

    async def ban_user(self, admin_id: int, target_telegram_id: int, reason: str = None) -> bool:
        """Ban a user."""
        result = await self.session.execute(
            select(User).where(User.telegram_id == target_telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return False
        
        user.is_banned = True
        user.banned_at = datetime.utcnow()
        user.banned_by = admin_id
        
        # Log the action
        log = AdminLog(
            admin_id=admin_id,
            action="ban_user",
            target_user_id=user.id,
            details=reason
        )
        self.session.add(log)
        await self.session.flush()
        return True

    async def unban_user(self, admin_id: int, target_telegram_id: int) -> bool:
        """Unban a user."""
        result = await self.session.execute(
            select(User).where(User.telegram_id == target_telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return False
        
        user.is_banned = False
        user.banned_at = None
        user.banned_by = None
        
        # Log the action
        log = AdminLog(
            admin_id=admin_id,
            action="unban_user",
            target_user_id=user.id
        )
        self.session.add(log)
        await self.session.flush()
        return True

    async def make_admin(self, admin_id: int, target_telegram_id: int) -> bool:
        """Make a user an admin."""
        result = await self.session.execute(
            select(User).where(User.telegram_id == target_telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return False
        
        user.is_admin = True
        
        # Log the action
        log = AdminLog(
            admin_id=admin_id,
            action="add_admin",
            target_user_id=user.id
        )
        self.session.add(log)
        await self.session.flush()
        return True

    async def remove_admin(self, admin_id: int, target_telegram_id: int) -> bool:
        """Remove admin privileges from a user."""
        result = await self.session.execute(
            select(User).where(User.telegram_id == target_telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return False
        
        # Cannot remove master admins
        if self.is_master_admin(user.username):
            return False
        
        user.is_admin = False
        
        # Log the action
        log = AdminLog(
            admin_id=admin_id,
            action="remove_admin",
            target_user_id=user.id
        )
        self.session.add(log)
        await self.session.flush()
        return True

    async def create_invite_code(
        self, 
        admin_id: int, 
        invite_type: str = "user",
        max_uses: int = None
    ) -> InviteCode:
        """Create a new invite code."""
        code = secrets.token_urlsafe(8)
        
        invite = InviteCode(
            code=code,
            created_by=admin_id,
            invite_type=invite_type,
            max_uses=max_uses
        )
        self.session.add(invite)
        
        # Log the action
        log = AdminLog(
            admin_id=admin_id,
            action="create_invite",
            details=f"type={invite_type}, code={code}"
        )
        self.session.add(log)
        await self.session.flush()
        return invite

    async def get_invite_by_code(self, code: str) -> Optional[InviteCode]:
        """Get invite by code."""
        result = await self.session.execute(
            select(InviteCode).where(
                InviteCode.code == code,
                InviteCode.is_active == True
            )
        )
        return result.scalar_one_or_none()

    async def use_invite_code(self, code: str, user_id: int) -> bool:
        """Mark an invite code as used."""
        invite = await self.get_invite_by_code(code)
        if not invite:
            return False
        
        # Check if max uses reached
        if invite.max_uses and invite.uses_count >= invite.max_uses:
            return False
        
        invite.uses_count += 1
        
        # Deactivate if max uses reached
        if invite.max_uses and invite.uses_count >= invite.max_uses:
            invite.is_active = False
        
        await self.session.flush()
        return True

    async def get_admin_logs(self, limit: int = 50) -> List[AdminLog]:
        """Get recent admin logs."""
        result = await self.session.execute(
            select(AdminLog)
            .order_by(AdminLog.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_next_registration_number(self) -> int:
        """Get the next registration number."""
        result = await self.session.execute(
            select(func.max(User.registration_number))
        )
        max_num = result.scalar() or 0
        return max_num + 1
