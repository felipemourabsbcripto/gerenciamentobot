#!/usr/bin/env python3
"""
Script para adicionar colunas faltantes na tabela futures_trades.
"""
import sqlite3

DB_PATH = '/Users/felipemoura/Desktop/gerenciamentobot/data/crypto_portfolio.db'

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Colunas que faltam
    columns_to_add = [
        ("side", "VARCHAR(10)"),
        ("status", "VARCHAR(20) DEFAULT 'open'"),
        ("pnl", "FLOAT"),
        ("pnl_percent", "FLOAT"),
        ("is_altcoin", "BOOLEAN DEFAULT 0"),
        ("risk_level", "VARCHAR(20) DEFAULT 'normal'"),
        ("current_price", "FLOAT"),
        ("opened_at", "DATETIME"),
    ]
    
    # Verificar colunas existentes
    cursor.execute("PRAGMA table_info(futures_trades)")
    existing = {row[1] for row in cursor.fetchall()}
    
    for col_name, col_type in columns_to_add:
        if col_name not in existing:
            try:
                cursor.execute(f"ALTER TABLE futures_trades ADD COLUMN {col_name} {col_type}")
                print(f"✅ Adicionada coluna: {col_name}")
            except Exception as e:
                print(f"⚠️ Erro ao adicionar {col_name}: {e}")
    
    # Copiar valores de direction para side (se direction existir)
    if 'direction' in existing:
        cursor.execute("UPDATE futures_trades SET side = direction WHERE side IS NULL")
        print("✅ Copiado direction -> side")
    
    # Copiar is_open para status
    if 'is_open' in existing:
        cursor.execute("UPDATE futures_trades SET status = CASE WHEN is_open = 1 THEN 'open' ELSE 'closed' END WHERE status IS NULL")
        print("✅ Convertido is_open -> status")
    
    # Copiar realized_pnl para pnl
    if 'realized_pnl' in existing:
        cursor.execute("UPDATE futures_trades SET pnl = realized_pnl WHERE pnl IS NULL")
        print("✅ Copiado realized_pnl -> pnl")
    
    # Copiar created_at para opened_at
    cursor.execute("UPDATE futures_trades SET opened_at = created_at WHERE opened_at IS NULL")
    print("✅ Copiado created_at -> opened_at")
    
    conn.commit()
    conn.close()
    print("\n🎉 Migração concluída!")

if __name__ == "__main__":
    migrate()
