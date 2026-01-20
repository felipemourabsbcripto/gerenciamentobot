#!/usr/bin/env python3
"""
Database migration script to add new columns for user registration and admin features.
"""
import asyncio
import aiosqlite
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "data" / "crypto_portfolio.db"

# New columns to add to users table
USER_COLUMNS = [
    ("registration_number", "INTEGER"),
    ("full_name", "VARCHAR(255)"),
    ("phone", "VARCHAR(50)"),
    ("birth_date", "VARCHAR(20)"),
    ("is_registered", "BOOLEAN DEFAULT 0"),
    ("accepted_terms", "BOOLEAN DEFAULT 0"),
    ("accepted_terms_at", "DATETIME"),
    ("futures_balance", "FLOAT DEFAULT 0.0"),
    ("futures_risk_percent", "FLOAT DEFAULT 5.0"),
    ("is_admin", "BOOLEAN DEFAULT 0"),
    ("is_banned", "BOOLEAN DEFAULT 0"),
    ("banned_at", "DATETIME"),
    ("banned_by", "INTEGER"),
    ("invited_by", "INTEGER"),
    ("invite_code", "VARCHAR(50)"),
    # Configurações de alertas personalizados
    ("price_alerts_enabled", "BOOLEAN DEFAULT 1"),
    ("check_interval_minutes", "INTEGER DEFAULT 5"),
]

# New columns to add to futures_trades table
FUTURES_COLUMNS = [
    ("stop_percent", "FLOAT"),
    ("risk_usd", "FLOAT"),
    ("timeframe", "VARCHAR(10)"),
    ("zone_used", "VARCHAR(20)"),
    ("target_1_price", "FLOAT"),
    ("target_1_percent", "FLOAT"),
    ("target_2_price", "FLOAT"),
    ("target_2_percent", "FLOAT"),
    ("target_3_price", "FLOAT"),
    ("target_3_percent", "FLOAT"),
    ("allocation_percent", "FLOAT"),
]

# New tables to create
NEW_TABLES = [
    """
    CREATE TABLE IF NOT EXISTS invite_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code VARCHAR(50) UNIQUE NOT NULL,
        created_by INTEGER NOT NULL REFERENCES users(id),
        invite_type VARCHAR(20) DEFAULT 'user',
        uses_count INTEGER DEFAULT 0,
        max_uses INTEGER,
        is_active BOOLEAN DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS admin_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER NOT NULL REFERENCES users(id),
        action VARCHAR(100) NOT NULL,
        target_user_id INTEGER,
        details TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
]


async def migrate():
    """Run database migration."""
    print(f"🔧 Migrando banco de dados: {DATABASE_PATH}")
    
    if not os.path.exists(DATABASE_PATH):
        print("❌ Banco de dados não encontrado!")
        return
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Get existing columns in users table
        cursor = await db.execute("PRAGMA table_info(users)")
        existing_columns = {row[1] for row in await cursor.fetchall()}
        print(f"📋 Colunas existentes em users: {len(existing_columns)}")
        
        # Add new columns to users table
        for col_name, col_type in USER_COLUMNS:
            if col_name not in existing_columns:
                try:
                    await db.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                    print(f"  ✅ Adicionada coluna users.{col_name}")
                except Exception as e:
                    print(f"  ⚠️ Coluna users.{col_name}: {e}")
        
        # Get existing columns in futures_trades table
        cursor = await db.execute("PRAGMA table_info(futures_trades)")
        futures_columns = {row[1] for row in await cursor.fetchall()}
        print(f"📋 Colunas existentes em futures_trades: {len(futures_columns)}")
        
        # Add new columns to futures_trades table
        for col_name, col_type in FUTURES_COLUMNS:
            if col_name not in futures_columns:
                try:
                    await db.execute(f"ALTER TABLE futures_trades ADD COLUMN {col_name} {col_type}")
                    print(f"  ✅ Adicionada coluna futures_trades.{col_name}")
                except Exception as e:
                    print(f"  ⚠️ Coluna futures_trades.{col_name}: {e}")
        
        # Create new tables
        for table_sql in NEW_TABLES:
            try:
                await db.execute(table_sql)
                print(f"  ✅ Tabela criada/verificada")
            except Exception as e:
                print(f"  ⚠️ Erro criando tabela: {e}")
        
        # Mark existing users as registered (for backwards compatibility)
        await db.execute("""
            UPDATE users 
            SET is_registered = 1, 
                accepted_terms = 1,
                full_name = COALESCE(first_name, '') || ' ' || COALESCE(last_name, '')
            WHERE is_registered IS NULL OR is_registered = 0
        """)
        print("  ✅ Usuários existentes marcados como registrados")
        
        # Set default futures_risk_percent for existing users
        await db.execute("""
            UPDATE users 
            SET futures_risk_percent = 5.0 
            WHERE futures_risk_percent IS NULL
        """)
        print("  ✅ Risco de futuros padrão definido (5%)")
        
        # Assign registration numbers to existing users
        await db.execute("""
            UPDATE users 
            SET registration_number = id 
            WHERE registration_number IS NULL
        """)
        print("  ✅ Números de registro atribuídos")
        
        await db.commit()
        print("\n✅ Migração concluída com sucesso!")


if __name__ == "__main__":
    asyncio.run(migrate())
