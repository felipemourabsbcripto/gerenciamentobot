"""
Test script for database operations.
"""
import asyncio
import pytest
from src.database import db, UserRepository, AssetRepository

pytest_plugins = ('pytest_asyncio',)


@pytest.mark.asyncio
async def test():
    # Inicializar banco de dados
    await db.init_db()
    print('✅ Banco de dados inicializado')
    
    # Testar criar usuário
    async with db.get_session() as session:
        user_repo = UserRepository(session)
        asset_repo = AssetRepository(session)
        
        user = await user_repo.get_or_create(
            telegram_id=123456789,
            username='test_user',
            first_name='Test',
            last_name='User'
        )
        print(f'✅ Usuário criado/encontrado: {user.username} (ID: {user.id})')
        
        # Testar criar ativo (verificar se já existe primeiro)
        existing = await asset_repo.get_user_asset_by_coin(user.id, 'bitcoin')
        if existing:
            asset = existing
            print(f'✅ Ativo existente: {asset.name} ({asset.symbol})')
        else:
            asset = await asset_repo.create(
                user_id=user.id,
                coin_id='bitcoin',
                symbol='BTC',
                name='Bitcoin',
                quantity=0.5,
                purchase_price=85000.0
            )
            print(f'✅ Ativo criado: {asset.name} ({asset.symbol})')
        
        # Listar ativos
        assets = await asset_repo.get_user_assets(user.id)
        print(f'✅ Total de ativos do usuário: {len(assets)}')
    
    await db.close()
    print('\n🎉 Testes do banco de dados concluídos!')


if __name__ == "__main__":
    asyncio.run(test())
