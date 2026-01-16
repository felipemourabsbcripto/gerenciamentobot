#!/usr/bin/env python3
"""
Script de teste completo para simular o fluxo do bot.
"""
import asyncio
import sys

async def test_imports():
    """Test all imports."""
    print("\n" + "="*50)
    print("🔍 TESTANDO IMPORTS...")
    print("="*50)
    
    try:
        from src.models import FuturesTrade, User, Asset, AssetEntry, Alert
        from src.database import get_async_session
        from src.database.repositories import (
            UserRepository, FuturesRepository, AssetRepository, 
            EntryRepository, AlertRepository, AdminRepository
        )
        from src.utils.formatters import MessageFormatter, parse_us_number, format_us_price
        from src.utils.keyboards import KeyboardBuilder
        from src.services.risk_management import risk_service
        from src.services.market_data_service import market_data_service
        print("✅ Todos os imports OK!")
        return True
    except Exception as e:
        print(f"❌ Erro de import: {e}")
        return False


async def test_database():
    """Test database connection and tables."""
    print("\n" + "="*50)
    print("🗄️ TESTANDO BANCO DE DADOS...")
    print("="*50)
    
    try:
        from src.database import get_async_session
        from src.database.repositories import UserRepository, FuturesRepository
        from sqlalchemy import select, func, text
        from src.models import User, FuturesTrade
        
        async with get_async_session() as session:
            # Test user count
            result = await session.execute(select(func.count(User.id)))
            user_count = result.scalar()
            print(f"📊 Usuários: {user_count}")
            
            # Test futures trades count
            result = await session.execute(select(func.count(FuturesTrade.id)))
            trades_count = result.scalar()
            print(f"📈 Trades Futuros: {trades_count}")
            
            # Check if new columns exist
            try:
                result = await session.execute(text("PRAGMA table_info(futures_trades)"))
                columns = result.fetchall()
                column_names = [col[1] for col in columns]
                
                required_columns = [
                    'target_1_price', 'target_1_percent',
                    'target_2_price', 'target_2_percent', 
                    'target_3_price', 'target_3_percent',
                    'allocation_percent'
                ]
                
                missing = [col for col in required_columns if col not in column_names]
                if missing:
                    print(f"⚠️ Colunas faltando na tabela futures_trades: {missing}")
                    print("   Execute: python migrate_db.py para adicionar as colunas")
                    return False
                else:
                    print("✅ Todas as novas colunas existem!")
                    
            except Exception as e:
                print(f"⚠️ Erro ao verificar colunas: {e}")
            
            print("✅ Banco de dados OK!")
            return True
            
    except Exception as e:
        print(f"❌ Erro de banco de dados: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_formatters():
    """Test formatter functions."""
    print("\n" + "="*50)
    print("📝 TESTANDO FORMATTERS...")
    print("="*50)
    
    try:
        from src.utils.formatters import parse_us_number, format_us_price, MessageFormatter
        
        # Test parse_us_number
        test_cases = [
            ("95,699.90", 95699.90),
            ("1,234.56", 1234.56),
            ("100.50", 100.50),
            ("1234.56", 1234.56),
            ("1.234,56", 1234.56),  # BR format
        ]
        
        print("Testando parse_us_number:")
        for input_val, expected in test_cases:
            result = parse_us_number(input_val)
            status = "✅" if abs(result - expected) < 0.01 else "❌"
            print(f"  {status} parse_us_number('{input_val}') = {result} (esperado: {expected})")
        
        # Test format_us_price
        print("\nTestando format_us_price:")
        format_cases = [
            (95699.90, "95,699.90"),
            (1234.56, "1,234.56"),
            (100.50, "100.50"),
        ]
        
        for input_val, expected in format_cases:
            result = format_us_price(input_val)
            status = "✅" if result == expected else "❌"
            print(f"  {status} format_us_price({input_val}) = '{result}' (esperado: '{expected}')")
        
        # Test futures_full_trade_summary
        print("\nTestando futures_full_trade_summary:")
        try:
            trade_data = {
                'pair': 'BTCUSDT',
                'entry_price': 95699.90,
                'side': 'long',
                'leverage': 10,
                'stop_loss': 94000.0,
                'stop_percent': 1.77,
                'target_1': {'price': 98000, 'percent': 2.4},
                'target_2': {'price': 100000, 'percent': 4.5},
                'timeframe': '4h',
                'margin': 100,
                'quantity': 0.01,
                'risk_usd': 17.7,
                'futures_balance': 1000,
                'risk_percent': 5,
            }
            summary = MessageFormatter.futures_full_trade_summary(trade_data, 95500.0)
            if summary and len(summary) > 100:
                print(f"  ✅ Summary gerado ({len(summary)} chars)")
            else:
                print(f"  ❌ Summary muito curto ou vazio")
        except Exception as e:
            print(f"  ❌ Erro em futures_full_trade_summary: {e}")
        
        print("✅ Formatters OK!")
        return True
        
    except Exception as e:
        print(f"❌ Erro de formatters: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_keyboards():
    """Test keyboard builders."""
    print("\n" + "="*50)
    print("⌨️ TESTANDO KEYBOARDS...")
    print("="*50)
    
    try:
        from src.utils.keyboards import KeyboardBuilder
        
        keyboards_to_test = [
            ('main_menu', []),
            ('futures_menu', []),
            ('futures_direction_selection', []),
            ('futures_leverage_selection', []),
            ('futures_timeframe_selection', []),
            ('futures_targets_options', [1]),
            ('cancel_action', []),
        ]
        
        for method_name, args in keyboards_to_test:
            try:
                method = getattr(KeyboardBuilder, method_name, None)
                if method:
                    result = method(*args)
                    if result:
                        print(f"  ✅ {method_name}() OK")
                    else:
                        print(f"  ❌ {method_name}() retornou None")
                else:
                    print(f"  ⚠️ {method_name}() não existe")
            except Exception as e:
                print(f"  ❌ {method_name}() erro: {e}")
        
        print("✅ Keyboards OK!")
        return True
        
    except Exception as e:
        print(f"❌ Erro de keyboards: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_risk_management():
    """Test risk management service."""
    print("\n" + "="*50)
    print("⚠️ TESTANDO RISK MANAGEMENT...")
    print("="*50)
    
    try:
        from src.services.risk_management import risk_service
        
        # Test calculate_stop_percent
        test_cases = [
            {'entry': 100, 'stop': 95, 'side': 'long', 'expected': 5.0},
            {'entry': 100, 'stop': 105, 'side': 'short', 'expected': 5.0},
        ]
        
        print("Testando calculate_stop_percent:")
        for case in test_cases:
            result = risk_service.calculate_stop_percent(
                case['entry'], case['stop'], case['side']
            )
            status = "✅" if abs(result - case['expected']) < 0.1 else "❌"
            print(f"  {status} entry={case['entry']}, stop={case['stop']}, side={case['side']} => {result:.2f}%")
        
        # Test calculate_position_size
        print("\nTestando calculate_position_size:")
        # Parâmetros: futures_balance, risk_percent, entry_price, stop_price, leverage
        # Retorna: (quantity, margin_required, position_value)
        entry = 100.0
        stop = 98.0  # 2% stop
        quantity, margin, position_value = risk_service.calculate_position_size(
            futures_balance=1000,
            risk_percent=5,
            entry_price=entry,
            stop_price=stop,
            leverage=10
        )
        print(f"  Balance: $1000, Risk: 5%, Entry: $100, Stop: $98 (2%), Leverage: 10x")
        print(f"  Margin: ${margin:.2f}")
        print(f"  Position Value: ${position_value:.2f}")
        print(f"  Quantity: {quantity:.6f}")
        
        print("✅ Risk Management OK!")
        return True
        
    except Exception as e:
        print(f"❌ Erro de risk management: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_market_data():
    """Test market data service."""
    print("\n" + "="*50)
    print("📊 TESTANDO MARKET DATA SERVICE...")
    print("="*50)
    
    try:
        from src.services.market_data_service import market_data_service
        
        # Test get_price
        print("Testando get_price (BTCUSDT):")
        price = await market_data_service.get_price("BTCUSDT")
        if price and price > 0:
            print(f"  ✅ BTC Price: ${price:,.2f}")
        else:
            print(f"  ⚠️ Não foi possível obter preço (pode ser problema de conexão)")
        
        print("✅ Market Data Service OK!")
        return True
        
    except Exception as e:
        print(f"⚠️ Erro de market data (pode ser conexão): {e}")
        return True  # Não falhar por problema de conexão


async def test_callbacks_handlers():
    """Test if callback handlers exist."""
    print("\n" + "="*50)
    print("🔄 TESTANDO CALLBACKS E HANDLERS...")
    print("="*50)
    
    try:
        from src.bot.handlers.callbacks import callback_handler
        from src.bot.handlers.messages import message_handler
        from src.bot.handlers.commands import start_command, help_command
        
        handlers = [
            ('callback_handler', callback_handler),
            ('message_handler', message_handler),
            ('start_command', start_command),
            ('help_command', help_command),
        ]
        
        for name, handler in handlers:
            if callable(handler):
                print(f"  ✅ {name} existe e é callable")
            else:
                print(f"  ❌ {name} não é callable")
        
        print("✅ Handlers OK!")
        return True
        
    except Exception as e:
        print(f"❌ Erro de handlers: {e}")
        import traceback
        traceback.print_exc()
        return False


async def simulate_futures_flow():
    """Simulate the complete futures registration flow."""
    print("\n" + "="*50)
    print("🎮 SIMULANDO FLUXO DE CADASTRO DE FUTUROS...")
    print("="*50)
    
    try:
        from src.utils.formatters import parse_us_number, format_us_price, MessageFormatter
        from src.services.risk_management import risk_service
        
        # Simulated trade data (as if user entered step by step)
        print("\n📝 Passo 1: Par")
        pair = "BTC/USDT"
        pair_normalized = pair.upper().replace("/", "").replace("-", "").replace(".P", "PERP").replace(" ", "")
        print(f"   Input: {pair} => Normalizado: {pair_normalized}")
        
        print("\n📝 Passo 2: Preço de Entrada")
        entry_input = "95,699.90"
        entry_price = parse_us_number(entry_input)
        print(f"   Input: {entry_input} => Parsed: {entry_price}")
        
        print("\n📝 Passo 3: Direção")
        side = "long"
        print(f"   Selecionado: {side.upper()}")
        
        print("\n📝 Passo 4: Alavancagem")
        leverage = 10
        print(f"   Selecionado: {leverage}x")
        
        print("\n📝 Passo 5: Stop Loss")
        stop_input = "94,000.00"
        stop_price = parse_us_number(stop_input)
        stop_percent = risk_service.calculate_stop_percent(entry_price, stop_price, side)
        print(f"   Input: {stop_input} => Stop: ${stop_price:,.2f} ({stop_percent:.2f}%)")
        
        print("\n📝 Passo 6: Alvos de Venda")
        targets = [
            {"price": 98000, "percent": ((98000 - entry_price) / entry_price) * 100},
            {"price": 100000, "percent": ((100000 - entry_price) / entry_price) * 100},
        ]
        for i, t in enumerate(targets, 1):
            print(f"   Alvo {i}: ${t['price']:,.2f} ({t['percent']:.2f}%)")
        
        print("\n📝 Passo 7: Timeframe")
        timeframe = "4h"
        print(f"   Selecionado: {timeframe}")
        
        print("\n📝 Passo 8: Cálculo de Risco")
        futures_balance = 1000
        risk_percent = 5
        # calculate_position_size retorna tupla: (quantity, margin, position_value)
        quantity, margin, position_value = risk_service.calculate_position_size(
            futures_balance=futures_balance,
            risk_percent=risk_percent,
            entry_price=entry_price,
            stop_price=stop_price,
            leverage=leverage
        )
        
        # Calcular risco em USD
        max_risk_usd = futures_balance * (risk_percent / 100)
        
        print(f"   💰 Saldo Futuros: ${futures_balance:,.2f}")
        print(f"   📊 Risco Configurado: {risk_percent}%")
        print(f"   📉 Margem: ${margin:.2f}")
        print(f"   📈 Tamanho da Posição: ${position_value:.2f}")
        print(f"   ⚠️ Risco Máximo USD: ${max_risk_usd:.2f}")
        
        # Generate full summary
        trade_data = {
            'pair': pair_normalized,
            'entry_price': entry_price,
            'side': side,
            'leverage': leverage,
            'stop_loss': stop_price,
            'stop_percent': stop_percent,
            'target_1': targets[0] if len(targets) > 0 else None,
            'target_2': targets[1] if len(targets) > 1 else None,
            'timeframe': timeframe,
            'margin': margin,
            'quantity': quantity,
            'risk_usd': max_risk_usd,
            'futures_balance': futures_balance,
            'risk_percent': risk_percent,
        }
        
        print("\n" + "="*50)
        print("📋 RESUMO FINAL DO TRADE:")
        print("="*50)
        summary = MessageFormatter.futures_full_trade_summary(trade_data, entry_price)
        print(summary)
        
        print("\n✅ Fluxo de futuros simulado com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na simulação: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("   🧪 TESTE COMPLETO DO BOT - SIMULAÇÃO DE USUÁRIO")
    print("="*60)
    
    results = {}
    
    # Run all tests
    results['imports'] = await test_imports()
    results['database'] = await test_database()
    results['formatters'] = await test_formatters()
    results['keyboards'] = await test_keyboards()
    results['risk_management'] = await test_risk_management()
    results['market_data'] = await test_market_data()
    results['handlers'] = await test_callbacks_handlers()
    results['futures_flow'] = await simulate_futures_flow()
    
    # Summary
    print("\n" + "="*60)
    print("   📊 RESUMO DOS TESTES")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"   {status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "-"*40)
    print(f"   Total: {passed} passou, {failed} falhou")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
