"""
Integração com CCXT para análise de mercado
"""
import ccxt
from src.utils.logger import get_logger

logger = get_logger(__name__)


def obter_exchanges_disponiveis():
    """Lista todas exchanges suportadas"""
    return ccxt.exchanges


def obter_todos_pares(exchange_id='binance'):
    """
    Obtém todos os pares disponíveis em uma exchange
    
    Args:
        exchange_id (str): ID da exchange (binance, okx, bybit, etc)
    
    Returns:
        dict: Informações de todos os pares
    """
    try:
        exchange_class = getattr(ccxt, exchange_id)
        exchange = exchange_class()
        
        markets = exchange.load_markets()
        
        # Separar por tipo
        spot_pairs = {}
        futures_pairs = {}
        
        for symbol, market in markets.items():
            info = {
                'symbol': symbol,
                'base': market['base'],
                'quote': market['quote'],
                'active': market['active'],
                'type': market['type'],
                'limits': market['limits']
            }
            
            if market['spot']:
                spot_pairs[symbol] = info
            
            if market['future'] or market['swap']:
                futures_pairs[symbol] = info
        
        logger.info(f"✅ {exchange_id}: {len(spot_pairs)} SPOT, {len(futures_pairs)} FUTUROS")
        
        return {
            'spot': spot_pairs,
            'futures': futures_pairs,
            'total': len(markets)
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter pares de {exchange_id}: {e}")
        return None


def buscar_moeda(termo_busca, exchange_id='binance', tipo='all'):
    """
    Busca moedas por termo
    
    Args:
        termo_busca (str): Termo para buscar (ex: 'DOGE', 'BTC')
        exchange_id (str): Exchange para buscar
        tipo (str): 'spot', 'futures' ou 'all'
    
    Returns:
        list: Lista de pares encontrados
    """
    try:
        pares = obter_todos_pares(exchange_id)
        
        if not pares:
            return []
        
        termo = termo_busca.upper()
        resultados = []
        
        # Buscar em SPOT
        if tipo in ['spot', 'all']:
            for symbol, info in pares['spot'].items():
                if (termo in symbol or 
                    termo == info['base'] or 
                    termo in info['base']):
                    resultados.append({
                        **info,
                        'market_type': 'SPOT'
                    })
        
        # Buscar em FUTUROS
        if tipo in ['futures', 'all']:
            for symbol, info in pares['futures'].items():
                if (termo in symbol or 
                    termo == info['base'] or 
                    termo in info['base']):
                    resultados.append({
                        **info,
                        'market_type': 'FUTUROS'
                    })
        
        logger.info(f"✅ Encontrados {len(resultados)} pares para '{termo_busca}'")
        return resultados
        
    except Exception as e:
        logger.error(f"❌ Erro na busca: {e}")
        return []


def obter_preco_atual(symbol, exchange_id='binance'):
    """
    Obtém preço atual de um ativo
    
    Args:
        symbol (str): Símbolo do par (ex: 'BTC/USDT')
        exchange_id (str): ID da exchange
    
    Returns:
        dict: Dados de preço
    """
    try:
        exchange_class = getattr(ccxt, exchange_id)
        exchange = exchange_class()
        
        ticker = exchange.fetch_ticker(symbol)
        
        # Calcular volatilidade aproximada
        if ticker['high'] and ticker['low']:
            volatilidade_24h = ((ticker['high'] - ticker['low']) / ticker['open']) * 100
        else:
            volatilidade_24h = 0
        
        return {
            'symbol': symbol,
            'preco_atual': ticker['last'],
            'bid': ticker['bid'],
            'ask': ticker['ask'],
            'preco_abertura': ticker['open'],
            'preco_max': ticker['high'],
            'preco_min': ticker['low'],
            'volume': ticker['baseVolume'],
            'variacao_pct': ticker['percentage'],
            'volatilidade_24h': round(volatilidade_24h, 2),
            'timestamp': ticker['timestamp']
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter preço de {symbol}: {e}")
        return None


def obter_book_orders(symbol, exchange_id='binance', limit=10):
    """
    Obtém order book (livro de ofertas)
    """
    try:
        exchange_class = getattr(ccxt, exchange_id)
        exchange = exchange_class()
        
        orderbook = exchange.fetch_order_book(symbol, limit)
        
        return {
            'bids': orderbook['bids'][:limit],  # Ordens de compra
            'asks': orderbook['asks'][:limit],  # Ordens de venda
            'timestamp': orderbook['timestamp']
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter order book: {e}")
        return None


# Manter compatibilidade com código antigo
def obter_analise_tradingview(symbol, exchange_id='binance'):
    """
    Wrapper para manter compatibilidade
    """
    dados = obter_preco_atual(f"{symbol}/USDT", exchange_id)
    
    if not dados:
        return None
    
    # Adaptar formato para o código existente
    return {
        'symbol': symbol,
        'preco_atual': dados['preco_atual'],
        'volatilidade_24h': dados['volatilidade_24h'],
        'preco_max': dados['preco_max'],
        'preco_min': dados['preco_min'],
        'volume': dados['volume'],
        'variacao_pct': dados['variacao_pct'],
        # Suportes e resistências baseados em preços 24h
        'suportes': {
            's1': dados['preco_min'],
            's2': dados['preco_min'] * 0.98,
            's3': dados['preco_min'] * 0.95
        },
        'resistencias': {
            'r1': dados['preco_max'],
            'r2': dados['preco_max'] * 1.02,
            'r3': dados['preco_max'] * 1.05
        },
        'rsi': 50,  # Placeholder (CCXT não fornece RSI direto)
        'recomendacao': 'NEUTRAL',
        'tendencia': 'LATERAL'
    }


if __name__ == '__main__':
    # Testes
    print("🧪 Testando CCXT...")
    
    # Listar exchanges
    print(f"\n📊 Exchanges disponíveis: {len(obter_exchanges_disponiveis())}")
    
    # Buscar DOGE
    resultados = buscar_moeda('DOGE', 'binance', 'all')
    print(f"\n🔍 Pares DOGE encontrados: {len(resultados)}")
    for r in resultados[:5]:
        print(f"  - {r['symbol']} ({r['market_type']})")
    
    # Preço BTC
    btc = obter_preco_atual('BTC/USDT', 'binance')
    if btc:
        print(f"\n💰 BTC/USDT: ${btc['preco_atual']:,.2f}")
        print(f"   Volatilidade 24h: {btc['volatilidade_24h']:.2f}%")
