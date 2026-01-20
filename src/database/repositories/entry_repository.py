"""
Repository for AssetEntry model database operations.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import AssetEntry, Asset


class EntryRepository:
    """Repository for AssetEntry database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_entry(self, asset_id: int, entry_price: float, 
                           quantity: float, total_value: float = None,
                           notes: str = None, entry_date: datetime = None,
                           user_id: int = None) -> AssetEntry:
        """Create a new entry for an asset."""
        if total_value is None:
            total_value = entry_price * quantity
        
        # Get user_id from asset if not provided
        if user_id is None:
            asset = await self.session.get(Asset, asset_id)
            if asset:
                user_id = asset.user_id
            else:
                raise ValueError(f"Asset {asset_id} not found")
        
        entry = AssetEntry(
            user_id=user_id,
            asset_id=asset_id,
            entry_price=entry_price,
            quantity=quantity,
            total_value=total_value,
            entry_date=entry_date or datetime.utcnow(),
            notes=notes
        )
        self.session.add(entry)
        await self.session.flush()
        
        # Recalculate asset average
        await self._recalculate_asset_average(asset_id)
        
        return entry

    async def _recalculate_asset_average(self, asset_id: int) -> None:
        """Recalculate asset average price from all entries."""
        asset = await self.session.get(Asset, asset_id)
        if not asset:
            return
            
        entries = await self.get_asset_entries(asset_id)
        
        if entries:
            total_qty = sum(e.quantity for e in entries)
            total_cost = sum(e.quantity * e.entry_price for e in entries)
            
            asset.total_invested = total_cost
            asset.average_price = total_cost / total_qty if total_qty > 0 else 0
        else:
            # Keep existing average_price if no entries
            pass
        
        await self.session.flush()

    async def get_by_id(self, entry_id: int) -> Optional[AssetEntry]:
        """Get entry by ID."""
        result = await self.session.execute(
            select(AssetEntry).where(AssetEntry.id == entry_id)
        )
        return result.scalar_one_or_none()

    async def get_asset_entries(self, asset_id: int) -> List[AssetEntry]:
        """Get all active entries for an asset."""
        result = await self.session.execute(
            select(AssetEntry).where(
                AssetEntry.asset_id == asset_id,
                AssetEntry.is_active == True
            ).order_by(AssetEntry.entry_date.desc())
        )
        return list(result.scalars().all())

    async def deactivate_entry(self, entry_id: int) -> Optional[AssetEntry]:
        """Deactivate an entry (soft delete)."""
        entry = await self.get_by_id(entry_id)
        if entry:
            entry.is_active = False
            await self.session.flush()
            
            # Recalculate asset average
            await self._recalculate_asset_average(entry.asset_id)
        
        return entry

    async def update_entry(self, entry_id: int, entry_price: float = None,
                           quantity: float = None, notes: str = None) -> Optional[AssetEntry]:
        """Update an entry."""
        entry = await self.get_by_id(entry_id)
        if entry:
            if entry_price is not None:
                entry.entry_price = entry_price
            if quantity is not None:
                entry.quantity = quantity
            if notes is not None:
                entry.notes = notes
            
            entry.total_value = entry.entry_price * entry.quantity
            await self.session.flush()
            
            # Recalculate asset average
            await self._recalculate_asset_average(entry.asset_id)
        
        return entry

    async def get_total_entries_count(self, asset_id: int) -> int:
        """Get count of active entries for an asset."""
        entries = await self.get_asset_entries(asset_id)
        return len(entries)
