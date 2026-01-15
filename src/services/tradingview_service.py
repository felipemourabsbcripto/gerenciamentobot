"""
TradingView service - Wrapper para compatibilidade.
Agora usa o MarketDataService com ccxt + ta (100% gratuito).
"""
from src.services.market_data_service import (
    MarketDataService,
    MarketData,
    market_data_service,
    CRYPTO_SYMBOLS
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Export aliases for backward compatibility
TradingViewService = MarketDataService
TradingViewData = MarketData
tradingview_service = market_data_service

# Re-export CRYPTO_SYMBOLS
__all__ = [
    'TradingViewService',
    'TradingViewData', 
    'tradingview_service',
    'CRYPTO_SYMBOLS',
    'MarketDataService',
    'MarketData',
    'market_data_service'
]

logger.info("TradingViewService initialized (using MarketDataService with ccxt + ta)")
