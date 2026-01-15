"""
Repository for Alert model database operations.
"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Alert


class AlertRepository:
    """Repository for Alert database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, alert_type: str, message: str,
                     asset_id: int = None, price_at_alert: float = None) -> Alert:
        """Create a new alert."""
        alert = Alert(
            user_id=user_id,
            asset_id=asset_id,
            alert_type=alert_type,
            message=message,
            price_at_alert=price_at_alert
        )
        self.session.add(alert)
        await self.session.flush()
        return alert

    async def get_user_alerts(self, user_id: int, limit: int = 10) -> List[Alert]:
        """Get recent alerts for a user."""
        result = await self.session.execute(
            select(Alert)
            .where(Alert.user_id == user_id)
            .order_by(Alert.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_unread_alerts(self, user_id: int) -> List[Alert]:
        """Get unread alerts for a user."""
        result = await self.session.execute(
            select(Alert)
            .where(
                Alert.user_id == user_id,
                Alert.is_read == False
            )
            .order_by(Alert.created_at.desc())
        )
        return list(result.scalars().all())

    async def mark_as_read(self, alert_id: int) -> Optional[Alert]:
        """Mark an alert as read."""
        result = await self.session.execute(
            select(Alert).where(Alert.id == alert_id)
        )
        alert = result.scalar_one_or_none()
        if alert:
            alert.is_read = True
            await self.session.flush()
        return alert

    async def mark_all_as_read(self, user_id: int) -> int:
        """Mark all user's alerts as read."""
        result = await self.session.execute(
            select(Alert).where(
                Alert.user_id == user_id,
                Alert.is_read == False
            )
        )
        alerts = result.scalars().all()
        count = 0
        for alert in alerts:
            alert.is_read = True
            count += 1
        await self.session.flush()
        return count

    async def has_recent_alert(self, user_id: int, asset_id: int, 
                               alert_type: str, hours: int = 24) -> bool:
        """Check if there's a recent alert of the same type for this asset."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        result = await self.session.execute(
            select(Alert).where(
                Alert.user_id == user_id,
                Alert.asset_id == asset_id,
                Alert.alert_type == alert_type,
                Alert.created_at >= cutoff
            )
        )
        return result.scalar_one_or_none() is not None

    async def delete_old_alerts(self, days: int = 30) -> int:
        """Delete alerts older than specified days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(Alert).where(Alert.created_at < cutoff)
        )
        alerts = result.scalars().all()
        count = 0
        for alert in alerts:
            await self.session.delete(alert)
            count += 1
        await self.session.flush()
        return count
