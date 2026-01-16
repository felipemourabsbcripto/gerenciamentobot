#!/usr/bin/env python3
"""Fix existing users."""
import asyncio
import aiosqlite
from pathlib import Path

DATABASE_PATH = Path(__file__).parent / "data" / "crypto_portfolio.db"

async def fix_users():
    print(f"DB: {DATABASE_PATH}")
    print(f"Exists: {DATABASE_PATH.exists()}")
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Update existing users
        await db.execute("""
            UPDATE users 
            SET is_registered = 1, 
                accepted_terms = 1,
                full_name = COALESCE(first_name, '') || ' ' || COALESCE(last_name, '')
            WHERE is_registered IS NULL OR is_registered = 0
        """)
        await db.execute("""
            UPDATE users 
            SET registration_number = id 
            WHERE registration_number IS NULL
        """)
        await db.commit()
        
        # Show users
        cursor = await db.execute("SELECT id, telegram_id, username, is_registered, registration_number FROM users")
        users = await cursor.fetchall()
        print("Users:")
        for u in users:
            print(f"  ID: {u[0]}, TG: {u[1]}, @{u[2]}, Reg: {u[3]}, RegNum: {u[4]}")
        
        # Check tables
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = await cursor.fetchall()
        print(f"\nTables: {[t[0] for t in tables]}")

if __name__ == "__main__":
    asyncio.run(fix_users())
