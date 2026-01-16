"""
Test script for database operations.
"""
import asyncio
from src.database import db, UserRepository, AssetRepository


async def test():
    # Inicializar banco de dados
    await db.init_db()
    print('✅ Banco de dados inicializado')
    
    # Testar criar usuário
    async with db.get_session() as session:
        user = await UserRepository.get_or_create(
            session,
            telegram_id=123456789,
            username='test_user',
            first_name='Test',
            last_name='User'
        )
        print(f'✅ Usuário criado/encontrado: {user.username} (ID: {user.id})')
        
        # Testar criar ativo
        asset = await AssetRepository.create(
            session,
            user_id=user.id,
            coin_id='bitcoin',
            symbol='BTC',
            name='Bitcoin',
            quantity=0.5,
            purchase_price=85000.0
        )
        print(f'✅ Ativo criado: {asset.name} ({asset.symbol})')
        
        # Listar ativos
        assets = await AssetRepository.get_user_assets(session, user.id)
        print(f'✅ Total de ativos do usuário: {len(assets)}')
    
    await db.close()
    print('\n🎉 Testes do banco de dados concluídos!')


if __name__ == "__main__":
    asyncio.run(test())
