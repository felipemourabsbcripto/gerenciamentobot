"""
Repository for managing USDT reserve allocations.
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from src.models.models import ReserveAllocation
from datetime import datetime


class ReserveRepository:
    """Repository for ReserveAllocation operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_allocation(
        self,
        user_id: int,
        allocation_type: str,
        amount: float,
        asset_id: int = None,
        asset_symbol: str = None,
        asset_quantity: float = None,
        asset_price: float = None,
        notes: str = None
    ) -> ReserveAllocation:
        """Create a new reserve allocation record."""
        allocation = ReserveAllocation(
            user_id=user_id,
            asset_id=asset_id,
            allocation_type=allocation_type,
            amount=amount,
            asset_symbol=asset_symbol,
            asset_quantity=asset_quantity,
            asset_price=asset_price,
            notes=notes,
            created_at=datetime.utcnow()
        )
        self.session.add(allocation)
        await self.session.flush()
        return allocation

    async def get_user_allocations(
        self,
        user_id: int,
        limit: int = 20
    ) -> List[ReserveAllocation]:
        """Get user's reserve allocations, most recent first."""
        result = await self.session.execute(
            select(ReserveAllocation)
            .where(ReserveAllocation.user_id == user_id)
            .order_by(desc(ReserveAllocation.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_total_deposited(self, user_id: int) -> float:
        """Get total USDT deposited to reserve."""
        result = await self.session.execute(
            select(ReserveAllocation)
            .where(
                ReserveAllocation.user_id == user_id,
                ReserveAllocation.allocation_type == "deposit"
            )
        )
        allocations = result.scalars().all()
        return sum(a.amount for a in allocations)

    async def get_total_allocated(self, user_id: int) -> float:
        """Get total USDT allocated to assets (new_asset + average_down)."""
        result = await self.session.execute(
            select(ReserveAllocation)
            .where(
                ReserveAllocation.user_id == user_id,
                ReserveAllocation.allocation_type.in_(["new_asset", "average_down"])
            )
        )
        allocations = result.scalars().all()
        return sum(a.amount for a in allocations)

    async def get_allocations_summary(self, user_id: int) -> dict:
        """Get a summary of reserve allocations."""
        allocations = await self.get_user_allocations(user_id, limit=100)
        
        deposits = sum(a.amount for a in allocations if a.allocation_type == "deposit")
        new_assets = sum(a.amount for a in allocations if a.allocation_type == "new_asset")
        average_downs = sum(a.amount for a in allocations if a.allocation_type == "average_down")
        withdrawals = sum(a.amount for a in allocations if a.allocation_type == "withdrawal")
        
        available = deposits - new_assets - average_downs - withdrawals
        
        return {
            "total_deposited": deposits,
            "allocated_new_assets": new_assets,
            "allocated_average_down": average_downs,
            "withdrawals": withdrawals,
            "available_reserve": max(0, available),
            "total_invested": new_assets + average_downs,
            "recent_allocations": allocations[:10]
        }

    async def get_allocations_by_asset(
        self,
        user_id: int,
        asset_symbol: str
    ) -> List[ReserveAllocation]:
        """Get allocations for a specific asset."""
        result = await self.session.execute(
            select(ReserveAllocation)
            .where(
                ReserveAllocation.user_id == user_id,
                ReserveAllocation.asset_symbol == asset_symbol.upper()
            )
            .order_by(desc(ReserveAllocation.created_at))
        )
        return result.scalars().all()
