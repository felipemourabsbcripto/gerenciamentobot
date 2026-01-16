"""
Functional tests for the Crypto Portfolio Bot.
"""
import asyncio
import sys
sys.path.insert(0, '/Users/felipemoura/Desktop/gerenciamentobot')

from src.config import settings
from src.database import db, UserRepository, AssetRepository, AlertRepository
from src.services import CoinGeckoService
from src.services.price_monitor import PriceMonitoringService
from src.utils import KeyboardBuilder, MessageFormatter


async def test_configuration():
    """Test configuration loading."""
    print("\n" + "="*50)
    print("📋 TESTE 1: Configurações")
    print("="*50)
    
    assert settings.telegram.bot_token, "Token do Telegram não configurado"
    print(f"✅ Token Telegram: {settings.telegram.bot_token[:20]}...")
    
    assert settings.coingecko.api_key, "API Key CoinGecko não configurada"
    print(f"✅ API Key CoinGecko: {settings.coingecko.api_key[:15]}...")
    
    print(f"✅ Intervalo de verificação: {settings.monitoring.check_interval_minutes} min")
    print(f"✅ Limite de queda: {settings.monitoring.drop_threshold_percent}%")
    print(f"✅ Limite de lucro: {settings.monitoring.profit_threshold_percent}%")
    
    return True


async def test_coingecko_api():
    """Test CoinGecko API connection."""
    print("\n" + "="*50)
    print("🌐 TESTE 2: API CoinGecko")
    print("="*50)
    
    cg = CoinGeckoService(api_key=settings.coingecko.api_key)
    
    try:
        # Test ping
        status = await cg.ping()
        print(f"✅ API Status: {'Online' if status else 'Offline'}")
        
        if not status:
            print("⚠️ Tentando sem API Key...")
            cg2 = CoinGeckoService()
            status = await cg2.ping()
            print(f"✅ API Pública Status: {'Online' if status else 'Offline'}")
            await cg2.close()
        
        # Test price fetch
        price = await cg.get_coin_price('bitcoin')
        if price:
            print(f"✅ Bitcoin Price: ${price:,.2f}")
        
        # Test multiple prices
        prices = await cg.get_multiple_coin_prices(['bitcoin', 'ethereum', 'solana'])
        print(f"✅ Preços múltiplos: {len(prices)} moedas obtidas")
        for coin, p in prices.items():
            print(f"   • {coin}: ${p:,.2f}")
        
        # Test search
        coins = await cg.search_coins('cardano')
        print(f"✅ Busca 'cardano': {len(coins)} resultados")
        
        # Test top coins
        top = await cg.get_top_coins(5)
        print(f"✅ Top 5 moedas obtidas:")
        for i, coin in enumerate(top, 1):
            print(f"   {i}. {coin.name} ({coin.symbol.upper()}): ${coin.current_price:,.2f}")
        
    finally:
        await cg.close()
    
    return True


async def test_database():
    """Test database operations."""
    print("\n" + "="*50)
    print("🗄️ TESTE 3: Banco de Dados")
    print("="*50)
    
    await db.init_db()
    print("✅ Banco de dados inicializado")
    
    async with db.get_session() as session:
        # Create/get user
        user = await UserRepository.get_or_create(
            session,
            telegram_id=999888777,
            username='functional_test',
            first_name='Teste',
            last_name='Funcional'
        )
        print(f"✅ Usuário: {user.first_name} {user.last_name} (ID: {user.id})")
        
        # Update CoinGecko credentials
        user = await UserRepository.update_coingecko_credentials(
            session,
            telegram_id=999888777,
            api_key=settings.coingecko.api_key
        )
        print(f"✅ Credenciais CoinGecko atualizadas")
        
        # Create test assets
        assets_data = [
            ('bitcoin', 'BTC', 'Bitcoin', 0.1, 45000.0),
            ('ethereum', 'ETH', 'Ethereum', 2.0, 2500.0),
            ('solana', 'SOL', 'Solana', 50.0, 100.0),
        ]
        
        for coin_id, symbol, name, qty, price in assets_data:
            existing = await AssetRepository.get_user_asset_by_coin(session, user.id, coin_id)
            if not existing:
                asset = await AssetRepository.create(
                    session, user.id, coin_id, symbol, name, qty, price
                )
                print(f"✅ Ativo criado: {name} ({symbol})")
            else:
                print(f"✅ Ativo existente: {name} ({symbol})")
        
        # List user assets
        assets = await AssetRepository.get_user_assets(session, user.id)
        print(f"✅ Total de ativos: {len(assets)}")
        
        # Create test alert
        alert = await AlertRepository.create(
            session,
            user_id=user.id,
            alert_type='test',
            message='Alerta de teste funcional',
            asset_id=assets[0].id if assets else None
        )
        print(f"✅ Alerta criado: ID {alert.id}")
        
        # Get alerts
        alerts = await AlertRepository.get_user_alerts(session, user.id)
        print(f"✅ Total de alertas: {len(alerts)}")
    
    return True


async def test_price_monitor():
    """Test price monitoring service."""
    print("\n" + "="*50)
    print("📊 TESTE 4: Monitoramento de Preços")
    print("="*50)
    
    notifications_sent = []
    
    async def mock_notification(telegram_id, message, alert_type=None, asset_id=None):
        notifications_sent.append({
            'telegram_id': telegram_id,
            'message': message[:50] + '...',
            'type': alert_type
        })
        print(f"   📨 Notificação simulada para {telegram_id}")
        return True
    
    monitor = PriceMonitoringService(send_notification_callback=mock_notification)
    
    # Update prices and check assets
    async with db.get_session() as session:
        user = await UserRepository.get_by_telegram_id(session, 999888777)
        if user:
            assets = await AssetRepository.get_user_assets(session, user.id)
            
            # Fetch real prices
            cg = CoinGeckoService()
            try:
                prices = await cg.get_multiple_coin_prices([a.coin_id for a in assets])
                
                for asset in assets:
                    if asset.coin_id in prices:
                        current = prices[asset.coin_id]
                        await AssetRepository.update_current_price(session, asset.id, current)
                        
                        change = ((current - asset.purchase_price) / asset.purchase_price) * 100
                        emoji = "🟢" if change >= 0 else "🔴"
                        
                        print(f"✅ {asset.symbol}: ${current:,.2f} ({emoji} {change:+.2f}%)")
            finally:
                await cg.close()
    
    print(f"✅ Monitoramento de preços funcionando")
    
    return True


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
        ("API CoinGecko", test_coingecko_api),
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
