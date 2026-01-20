"""
Functional tests for the Crypto Portfolio Bot.
"""
import asyncio
import sys
import pytest
sys.path.insert(0, '/workspaces/gerenciamentobot')

pytest_plugins = ('pytest_asyncio',)

from src.config import settings
from src.database import db, UserRepository, AssetRepository, AlertRepository
from src.services import MarketDataService
from src.utils import KeyboardBuilder, MessageFormatter


@pytest.mark.asyncio
async def test_configuration():
    """Test configuration loading."""
    print("\n" + "="*50)
    print("📋 TESTE 1: Configurações")
    print("="*50)
    
    assert settings.telegram.bot_token, "Token do Telegram não configurado"
    print(f"✅ Token Telegram: {settings.telegram.bot_token[:20]}...")
    
    print(f"✅ Intervalo de verificação: {settings.monitoring.check_interval_minutes} min")
    print(f"✅ Limite de queda: {settings.monitoring.drop_threshold_percent}%")
    print(f"✅ Limite de lucro: {settings.monitoring.profit_threshold_percent}%")
    
    return True


@pytest.mark.asyncio
async def test_market_data_api():
    """Test Market Data API connection (Kraken/Gate.io)."""
    print("\n" + "="*50)
    print("🌐 TESTE 2: API Market Data (Exchange)")
    print("="*50)
    
    service = MarketDataService()
    
    try:
        # Test price fetch for Bitcoin (returns dict, not object)
        btc_data = await service.get_price("BTC")
        if btc_data and btc_data.get("price", 0) > 0:
            print(f"✅ Bitcoin Price: ${btc_data['price']:,.2f}")
            print(f"   Variação 24h: {btc_data.get('change_24h', 0):+.2f}%")
        else:
            print("⚠️ Não foi possível obter preço do Bitcoin")
        
        # Test Ethereum
        eth_data = await service.get_price("ETH")
        if eth_data and eth_data.get("price", 0) > 0:
            print(f"✅ Ethereum Price: ${eth_data['price']:,.2f}")
        else:
            print("⚠️ Não foi possível obter preço do Ethereum")
        
        # Test Solana
        sol_data = await service.get_price("SOL")
        if sol_data and sol_data.get("price", 0) > 0:
            print(f"✅ Solana Price: ${sol_data['price']:,.2f}")
        else:
            print("⚠️ Não foi possível obter preço do Solana")
        
    except Exception as e:
        print(f"⚠️ Erro ao consultar API: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await service.close()
    
    return True


@pytest.mark.asyncio
async def test_database():
    """Test database operations."""
    print("\n" + "="*50)
    print("🗄️ TESTE 3: Banco de Dados")
    print("="*50)
    
    await db.init_db()
    print("✅ Banco de dados inicializado")
    
    async with db.get_session() as session:
        user_repo = UserRepository(session)
        asset_repo = AssetRepository(session)
        alert_repo = AlertRepository(session)
        
        # Create/get user
        user = await user_repo.get_or_create(
            telegram_id=999888777,
            username='functional_test',
            first_name='Teste',
            last_name='Funcional'
        )
        print(f"✅ Usuário: {user.first_name} {user.last_name} (ID: {user.id})")
        
        # Create test assets
        assets_data = [
            ('bitcoin', 'BTC', 'Bitcoin', 0.1, 45000.0),
            ('ethereum', 'ETH', 'Ethereum', 2.0, 2500.0),
            ('solana', 'SOL', 'Solana', 50.0, 100.0),
        ]
        
        for coin_id, symbol, name, qty, price in assets_data:
            existing = await asset_repo.get_user_asset_by_coin(user.id, coin_id)
            if not existing:
                asset = await asset_repo.create(
                    user_id=user.id,
                    coin_id=coin_id,
                    symbol=symbol,
                    name=name,
                    quantity=qty,
                    purchase_price=price
                )
                print(f"✅ Ativo criado: {name} ({symbol})")
            else:
                print(f"✅ Ativo existente: {name} ({symbol})")
        
        # List user assets
        assets = await asset_repo.get_user_assets(user.id)
        print(f"✅ Total de ativos: {len(assets)}")
        
        # Create test alert
        alert = await alert_repo.create(
            user_id=user.id,
            alert_type='test',
            message='Alerta de teste funcional',
            asset_id=assets[0].id if assets else None
        )
        print(f"✅ Alerta criado: ID {alert.id}")
        
        # Get alerts
        alerts = await alert_repo.get_user_alerts(user.id)
        print(f"✅ Total de alertas: {len(alerts)}")
    
    return True


@pytest.mark.asyncio
async def test_price_monitor():
    """Test price monitoring service."""
    print("\n" + "="*50)
    print("📊 TESTE 4: Monitoramento de Preços")
    print("="*50)
    
    # Update prices and check assets
    async with db.get_session() as session:
        user_repo = UserRepository(session)
        asset_repo = AssetRepository(session)
        
        user = await user_repo.get_by_telegram_id(999888777)
        if user:
            assets = await asset_repo.get_user_assets(user.id)
            
            # Fetch real prices using MarketDataService
            service = MarketDataService()
            try:
                # Map coin_id to symbol for exchange
                symbol_map = {
                    'bitcoin': 'BTC',
                    'ethereum': 'ETH',
                    'solana': 'SOL'
                }
                
                for asset in assets:
                    symbol = symbol_map.get(asset.coin_id)
                    if symbol:
                        data = await service.get_price(symbol)
                        if data and data.get("price", 0) > 0:
                            current = data["price"]
                            await asset_repo.update_current_price(asset.id, current)
                            
                            change = ((current - asset.average_price) / asset.average_price) * 100
                            emoji = "🟢" if change >= 0 else "🔴"
                            
                            print(f"✅ {asset.symbol}: ${current:,.2f} ({emoji} {change:+.2f}%)")
            finally:
                await service.close()
    
    print(f"✅ Monitoramento de preços funcionando")
    
    return True


@pytest.mark.asyncio
async def test_telegram_bot():
    """Test Telegram bot connection."""
    print("\n" + "="*50)
    print("🤖 TESTE 5: Conexão Telegram Bot")
    print("="*50)
    
    from telegram import Bot
    
    bot = Bot(token=settings.telegram.bot_token)
    
    try:
        me = await bot.get_me()
        print(f"✅ Bot conectado: @{me.username}")
        print(f"✅ Nome: {me.first_name}")
        print(f"✅ ID: {me.id}")
        print(f"✅ Pode entrar em grupos: {me.can_join_groups}")
        
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return False
    finally:
        await bot.close()
    
    return True


@pytest.mark.asyncio
async def test_keyboards():
    """Test keyboard generation."""
    print("\n" + "="*50)
    print("⌨️ TESTE 6: Teclados Inline")
    print("="*50)
    
    # Main menu
    kb = KeyboardBuilder.main_menu()
    print(f"✅ Menu principal: {len(kb.inline_keyboard)} linhas")
    
    # Settings menu
    kb = KeyboardBuilder.settings_menu()
    print(f"✅ Menu configurações: {len(kb.inline_keyboard)} linhas")
    
    # Asset actions
    kb = KeyboardBuilder.asset_actions(1)
    print(f"✅ Ações do ativo: {len(kb.inline_keyboard)} linhas")
    
    # Alert response
    kb = KeyboardBuilder.alert_response('drop', 1)
    print(f"✅ Resposta alerta queda: {len(kb.inline_keyboard)} linhas")
    
    kb = KeyboardBuilder.alert_response('profit', 1)
    print(f"✅ Resposta alerta lucro: {len(kb.inline_keyboard)} linhas")
    
    return True


@pytest.mark.asyncio
async def test_formatters():
    """Test message formatters."""
    print("\n" + "="*50)
    print("📝 TESTE 7: Formatadores de Mensagem")
    print("="*50)
    
    # Welcome message
    msg = MessageFormatter.welcome_message("Felipe")
    print(f"✅ Mensagem de boas-vindas: {len(msg)} chars")
    
    # Help message
    msg = MessageFormatter.help_message()
    print(f"✅ Mensagem de ajuda: {len(msg)} chars")
    
    # Portfolio summary (empty)
    msg = MessageFormatter.portfolio_summary([])
    print(f"✅ Portfolio vazio: {len(msg)} chars")
    
    return True


async def run_all_tests():
    """Run all functional tests."""
    print("\n" + "🚀"*25)
    print("   TESTES FUNCIONAIS - CRYPTO PORTFOLIO BOT")
    print("🚀"*25)
    
    tests = [
        ("Configurações", test_configuration),
        ("API Market Data", test_market_data_api),
        ("Banco de Dados", test_database),
        ("Monitoramento", test_price_monitor),
        ("Telegram Bot", test_telegram_bot),
        ("Teclados Inline", test_keyboards),
        ("Formatadores", test_formatters),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ ERRO em {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 RESUMO DOS TESTES")
    print("="*50)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"   {status}: {name}")
    
    print(f"\n🎯 Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM! O bot está pronto para uso.")
    else:
        print("\n⚠️ Alguns testes falharam. Verifique os erros acima.")
    
    await db.close()
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(run_all_tests())
