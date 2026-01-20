"""
Market Data Service - Substitui o TradingView usando ccxt + ta.
Dados de mercado via Binance API (gratuito) e indicadores calculados localmente.
"""
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import ccxt.async_support as ccxt

# Technical Analysis library
import ta
from ta.trend import SMAIndicator, EMAIndicator, MACD, ADXIndicator, IchimokuIndicator
from ta.momentum import RSIIndicator, StochasticOscillator, WilliamsRIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator, VolumeWeightedAveragePrice

from src.utils.logger import get_logger

logger = get_logger(__name__)


# Common crypto symbols
CRYPTO_SYMBOLS = {
    "BTC": "BTC/USDT",
    "ETH": "ETH/USDT",
    "BNB": "BNB/USDT",
    "SOL": "SOL/USDT",
    "XRP": "XRP/USDT",
    "ADA": "ADA/USDT",
    "DOGE": "DOGE/USDT",
    "DOT": "DOT/USDT",
    "MATIC": "MATIC/USDT",
    "SHIB": "SHIB/USDT",
    "LTC": "LTC/USDT",
    "AVAX": "AVAX/USDT",
    "LINK": "LINK/USDT",
    "UNI": "UNI/USDT",
    "ATOM": "ATOM/USDT",
    "XMR": "XMR/USDT",
    "ETC": "ETC/USDT",
    "XLM": "XLM/USDT",
    "BCH": "BCH/USDT",
    "APT": "APT/USDT",
    "FIL": "FIL/USDT",
    "NEAR": "NEAR/USDT",
    "ICP": "ICP/USDT",
    "VET": "VET/USDT",
    "ALGO": "ALGO/USDT",
    "FTM": "FTM/USDT",
    "SAND": "SAND/USDT",
    "MANA": "MANA/USDT",
    "AAVE": "AAVE/USDT",
    "AXS": "AXS/USDT",
    "THETA": "THETA/USDT",
    "EGLD": "EGLD/USDT",
    "XTZ": "XTZ/USDT",
    "EOS": "EOS/USDT",
    "ARB": "ARB/USDT",
    "OP": "OP/USDT",
    "INJ": "INJ/USDT",
    "SUI": "SUI/USDT",
    "SEI": "SEI/USDT",
    "TIA": "TIA/USDT",
    "JUP": "JUP/USDT",
    "WIF": "WIF/USDT",
    "PEPE": "PEPE/USDT",
    "BONK": "1000BONK/USDT",
}

# Timeframe mapping
TIMEFRAME_MAP = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "2h": "2h",
    "4h": "4h",
    "1d": "1d",
    "1w": "1w",
    "1M": "1M",
}


@dataclass
class MarketData:
    """Data class for market analysis result."""
    symbol: str
    exchange: str
    price: float
    change: float
    change_percent: float
    volume: float
    high: float
    low: float
    open_price: float
    recommendation: str  # BUY, SELL, NEUTRAL, STRONG_BUY, STRONG_SELL
    buy_signals: int
    sell_signals: int
    neutral_signals: int
    # Moving averages
    ma_10: Optional[float] = None
    ma_20: Optional[float] = None
    ma_50: Optional[float] = None
    ma_200: Optional[float] = None
    ema_10: Optional[float] = None
    ema_20: Optional[float] = None
    ema_50: Optional[float] = None
    ema_200: Optional[float] = None
    # Oscillators
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    stoch_k: Optional[float] = None
    stoch_d: Optional[float] = None
    adx: Optional[float] = None
    # Volatility
    atr: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    # Death/Golden Cross
    is_death_cross: bool = False
    is_golden_cross: bool = False
    # Timestamp
    timestamp: Optional[datetime] = None


class MarketDataService:
    """Service for fetching market data and calculating technical indicators."""

    def __init__(self):
        self._exchange = None
        self._cache: Dict[str, tuple] = {}  # symbol -> (data, timestamp)
        self._cache_ttl = 60  # Cache TTL in seconds
        logger.info("MarketDataService initialized")

    async def _get_exchange(self) -> ccxt.binance:
        """Get or create exchange instance. Uses Kraken as primary (works in US/EU)."""
        if self._exchange is None:
            # Use Kraken as primary - works in US and EU
            self._exchange = ccxt.kraken({
                'enableRateLimit': True,
            })
        return self._exchange
    
    async def _get_fallback_exchange(self):
        """Get fallback exchange (Gate.io) if primary fails."""
        return ccxt.gate({
            'enableRateLimit': True,
        })

    def _get_symbol(self, symbol: str) -> str:
        """Convert symbol to ccxt format."""
        symbol = symbol.upper().replace("-", "").replace("/", "")
        
        # Stablecoins - verificar ANTES de remover sufixos
        # USDT, USDC, BUSD, DAI, TUSD = 1.00 USD sempre
        clean_symbol = symbol.replace(".P", "")  # Remove perpetual suffix
        if clean_symbol in ["USDT", "USDC", "BUSD", "DAI", "TUSD"]:
            return None
        
        # Remove USDT suffix if present for lookup
        base = symbol.replace("USDT", "").replace("USD", "").replace(".P", "")
        
        # Verificar novamente após remover sufixos (caso base seja stablecoin)
        if base in ["USDT", "USDC", "BUSD", "DAI", "TUSD", ""]:
            return None
        
        # Check mapping
        if base in CRYPTO_SYMBOLS:
            return CRYPTO_SYMBOLS[base]
        
        # Default: add /USDT
        return f"{base}/USDT"

    async def _fetch_ohlcv(self, symbol: str, timeframe: str = "1d", limit: int = 250) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data from exchange with fallback."""
        ccxt_symbol = self._get_symbol(symbol)
        
        # Skip if symbol couldn't be mapped (e.g., stablecoins)
        if ccxt_symbol is None:
            logger.info(f"Skipping OHLCV fetch for {symbol} (stablecoin)")
            return None
        
        # Try primary exchange
        try:
            exchange = await self._get_exchange()
            ohlcv = await exchange.fetch_ohlcv(ccxt_symbol, timeframe, limit=limit)
            
            if ohlcv:
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                return df
                
        except Exception as e:
            logger.warning(f"Primary exchange failed for {symbol}: {e}")
        
        # Try fallback exchange
        try:
            fallback = await self._get_fallback_exchange()
            try:
                ohlcv = await fallback.fetch_ohlcv(ccxt_symbol, timeframe, limit=limit)
                
                if ohlcv:
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    return df
            finally:
                await fallback.close()
                
        except Exception as e:
            logger.error(f"Fallback exchange also failed for {symbol}: {e}")
        
        return None

    def _calculate_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all technical indicators using ta library."""
        indicators = {}
        
        try:
            close = df['close']
            high = df['high']
            low = df['low']
            volume = df['volume']
            
            # Moving Averages
            indicators['ma_10'] = SMAIndicator(close, window=10).sma_indicator().iloc[-1]
            indicators['ma_20'] = SMAIndicator(close, window=20).sma_indicator().iloc[-1]
            indicators['ma_50'] = SMAIndicator(close, window=50).sma_indicator().iloc[-1]
            indicators['ma_200'] = SMAIndicator(close, window=200).sma_indicator().iloc[-1] if len(df) >= 200 else None
            
            indicators['ema_10'] = EMAIndicator(close, window=10).ema_indicator().iloc[-1]
            indicators['ema_20'] = EMAIndicator(close, window=20).ema_indicator().iloc[-1]
            indicators['ema_50'] = EMAIndicator(close, window=50).ema_indicator().iloc[-1]
            indicators['ema_200'] = EMAIndicator(close, window=200).ema_indicator().iloc[-1] if len(df) >= 200 else None
            
            # MACD
            macd = MACD(close)
            indicators['macd'] = macd.macd().iloc[-1]
            indicators['macd_signal'] = macd.macd_signal().iloc[-1]
            indicators['macd_diff'] = macd.macd_diff().iloc[-1]
            
            # RSI
            indicators['rsi'] = RSIIndicator(close, window=14).rsi().iloc[-1]
            
            # Stochastic
            stoch = StochasticOscillator(high, low, close)
            indicators['stoch_k'] = stoch.stoch().iloc[-1]
            indicators['stoch_d'] = stoch.stoch_signal().iloc[-1]
            
            # ADX
            adx = ADXIndicator(high, low, close)
            indicators['adx'] = adx.adx().iloc[-1]
            indicators['adx_pos'] = adx.adx_pos().iloc[-1]
            indicators['adx_neg'] = adx.adx_neg().iloc[-1]
            
            # Bollinger Bands
            bb = BollingerBands(close)
            indicators['bb_upper'] = bb.bollinger_hband().iloc[-1]
            indicators['bb_middle'] = bb.bollinger_mavg().iloc[-1]
            indicators['bb_lower'] = bb.bollinger_lband().iloc[-1]
            
            # ATR
            indicators['atr'] = AverageTrueRange(high, low, close).average_true_range().iloc[-1]
            
            # Williams %R
            indicators['williams_r'] = WilliamsRIndicator(high, low, close).williams_r().iloc[-1]
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
        
        return indicators

    def _generate_recommendation(self, indicators: Dict[str, Any], price: float) -> tuple:
        """Generate buy/sell recommendation based on indicators."""
        buy_signals = 0
        sell_signals = 0
        neutral_signals = 0
        
        # RSI
        rsi = indicators.get('rsi')
        if rsi:
            if rsi < 30:
                buy_signals += 1
            elif rsi > 70:
                sell_signals += 1
            else:
                neutral_signals += 1
        
        # MACD
        macd_diff = indicators.get('macd_diff')
        if macd_diff:
            if macd_diff > 0:
                buy_signals += 1
            elif macd_diff < 0:
                sell_signals += 1
            else:
                neutral_signals += 1
        
        # Stochastic
        stoch_k = indicators.get('stoch_k')
        stoch_d = indicators.get('stoch_d')
        if stoch_k and stoch_d:
            if stoch_k < 20 and stoch_k > stoch_d:
                buy_signals += 1
            elif stoch_k > 80 and stoch_k < stoch_d:
                sell_signals += 1
            else:
                neutral_signals += 1
        
        # Moving Averages
        ma_20 = indicators.get('ma_20')
        ma_50 = indicators.get('ma_50')
        if ma_20 and ma_50:
            if price > ma_20 > ma_50:
                buy_signals += 1
            elif price < ma_20 < ma_50:
                sell_signals += 1
            else:
                neutral_signals += 1
        
        # EMA Cross
        ema_10 = indicators.get('ema_10')
        ema_20 = indicators.get('ema_20')
        if ema_10 and ema_20:
            if ema_10 > ema_20:
                buy_signals += 1
            elif ema_10 < ema_20:
                sell_signals += 1
            else:
                neutral_signals += 1
        
        # Bollinger Bands
        bb_upper = indicators.get('bb_upper')
        bb_lower = indicators.get('bb_lower')
        if bb_upper and bb_lower:
            if price < bb_lower:
                buy_signals += 1
            elif price > bb_upper:
                sell_signals += 1
            else:
                neutral_signals += 1
        
        # ADX (trend strength)
        adx = indicators.get('adx')
        adx_pos = indicators.get('adx_pos')
        adx_neg = indicators.get('adx_neg')
        if adx and adx > 25:
            if adx_pos and adx_neg:
                if adx_pos > adx_neg:
                    buy_signals += 1
                else:
                    sell_signals += 1
        else:
            neutral_signals += 1
        
        # Williams %R
        williams = indicators.get('williams_r')
        if williams:
            if williams < -80:
                buy_signals += 1
            elif williams > -20:
                sell_signals += 1
            else:
                neutral_signals += 1
        
        # Generate recommendation
        total = buy_signals + sell_signals + neutral_signals
        if total == 0:
            return "NEUTRAL", 0, 0, 0
        
        buy_ratio = buy_signals / total
        sell_ratio = sell_signals / total
        
        if buy_ratio >= 0.6:
            recommendation = "STRONG_BUY" if buy_ratio >= 0.75 else "BUY"
        elif sell_ratio >= 0.6:
            recommendation = "STRONG_SELL" if sell_ratio >= 0.75 else "SELL"
        else:
            recommendation = "NEUTRAL"
        
        return recommendation, buy_signals, sell_signals, neutral_signals

    async def get_analysis(self, symbol: str, interval: str = "1d") -> Optional[MarketData]:
        """Get full technical analysis for a symbol."""
        try:
            # Primeiro limpa o símbolo para identificar stablecoins
            # IMPORTANTE: Verificar ANTES de remover sufixos para capturar "USDT" puro
            upper_symbol = symbol.upper().replace(".P", "").replace("/", "").replace("-", "")
            
            # Lista de stablecoins
            STABLECOINS = ["USDT", "USDC", "BUSD", "DAI", "TUSD"]
            
            # Verificar se é stablecoin diretamente
            if upper_symbol in STABLECOINS:
                return MarketData(
                    symbol=upper_symbol,
                    exchange="STABLECOIN",
                    price=1.0,  # 1 stablecoin = 1 USD sempre
                    change=0.0,
                    change_percent=0.0,
                    volume=0.0,
                    high=1.0,
                    low=1.0,
                    open_price=1.0,
                    recommendation="NEUTRAL",
                    buy_signals=0,
                    sell_signals=0,
                    neutral_signals=1,
                    timestamp=datetime.now()
                )
            
            # Agora limpa para extrair o base symbol
            clean_symbol = upper_symbol.replace("USDT", "").replace("USD", "")
            
            # Verificar se após limpeza é stablecoin ou vazio
            if clean_symbol in STABLECOINS or clean_symbol == "":
                # Se sobrou uma stablecoin ou vazio, retorna 1.0
                final_symbol = clean_symbol if clean_symbol else upper_symbol
                return MarketData(
                    symbol=final_symbol if final_symbol else "USDT",
                    exchange="STABLECOIN",
                    price=1.0,
                    change=0.0,
                    change_percent=0.0,
                    volume=0.0,
                    high=1.0,
                    low=1.0,
                    open_price=1.0,
                    recommendation="NEUTRAL",
                    buy_signals=0,
                    sell_signals=0,
                    neutral_signals=1,
                    timestamp=datetime.now()
                )
            
            # Check cache
            cache_key = f"{symbol}_{interval}"
            if cache_key in self._cache:
                cached_data, cached_time = self._cache[cache_key]
                if (datetime.now() - cached_time).seconds < self._cache_ttl:
                    return cached_data
            
            # Fetch OHLCV data
            timeframe = TIMEFRAME_MAP.get(interval, "1d")
            df = await self._fetch_ohlcv(symbol, timeframe)
            
            if df is None or df.empty:
                return None
            
            # Get current price data
            price = df['close'].iloc[-1]
            open_price = df['open'].iloc[-1]
            high = df['high'].iloc[-1]
            low = df['low'].iloc[-1]
            volume = df['volume'].iloc[-1]
            change = price - open_price
            change_percent = (change / open_price * 100) if open_price else 0
            
            # Calculate indicators
            indicators = self._calculate_indicators(df)
            
            # Generate recommendation
            recommendation, buy_signals, sell_signals, neutral_signals = self._generate_recommendation(indicators, price)
            
            # Detect Death/Golden Cross
            ma_50 = indicators.get('ma_50')
            ma_200 = indicators.get('ma_200')
            is_death_cross = False
            is_golden_cross = False
            
            if ma_50 and ma_200:
                is_death_cross = ma_50 < ma_200
                is_golden_cross = ma_50 > ma_200
            
            # Create result
            result = MarketData(
                symbol=symbol.upper().replace("/", ""),
                exchange="BINANCE",
                price=price,
                change=change,
                change_percent=change_percent,
                volume=volume,
                high=high,
                low=low,
                open_price=open_price,
                recommendation=recommendation,
                buy_signals=buy_signals,
                sell_signals=sell_signals,
                neutral_signals=neutral_signals,
                ma_10=indicators.get('ma_10'),
                ma_20=indicators.get('ma_20'),
                ma_50=ma_50,
                ma_200=ma_200,
                ema_10=indicators.get('ema_10'),
                ema_20=indicators.get('ema_20'),
                ema_50=indicators.get('ema_50'),
                ema_200=indicators.get('ema_200'),
                rsi=indicators.get('rsi'),
                macd=indicators.get('macd'),
                macd_signal=indicators.get('macd_signal'),
                stoch_k=indicators.get('stoch_k'),
                stoch_d=indicators.get('stoch_d'),
                adx=indicators.get('adx'),
                atr=indicators.get('atr'),
                bb_upper=indicators.get('bb_upper'),
                bb_middle=indicators.get('bb_middle'),
                bb_lower=indicators.get('bb_lower'),
                is_death_cross=is_death_cross,
                is_golden_cross=is_golden_cross,
                timestamp=datetime.now()
            )
            
            # Cache result
            self._cache[cache_key] = (result, datetime.now())
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting analysis for {symbol}: {e}")
            return None

    async def get_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current price for a symbol."""
        analysis = await self.get_analysis(symbol)
        if analysis:
            return {
                "symbol": analysis.symbol,
                "price": analysis.price,
                "change_24h": analysis.change_percent,
                "high_24h": analysis.high,
                "low_24h": analysis.low,
                "volume": analysis.volume,
                "exchange": analysis.exchange
            }
        return None

    async def search_coins(self, query: str) -> List[Dict[str, Any]]:
        """Search for coins by symbol."""
        query = query.upper()
        results = []
        
        # Check if exact match in our mapping
        if query in CRYPTO_SYMBOLS or query.replace("USDT", "") in CRYPTO_SYMBOLS:
            base = query.replace("USDT", "")
            analysis = await self.get_analysis(base)
            if analysis:
                results.append({
                    "symbol": base,
                    "name": base,
                    "price": analysis.price,
                    "change_24h": analysis.change_percent,
                    "recommendation": analysis.recommendation
                })
        else:
            # Try to find matches
            matching_symbols = [s for s in CRYPTO_SYMBOLS.keys() if query in s]
            
            if not matching_symbols:
                # Try the query directly
                analysis = await self.get_analysis(query)
                if analysis:
                    results.append({
                        "symbol": query,
                        "name": query,
                        "price": analysis.price,
                        "change_24h": analysis.change_percent,
                        "recommendation": analysis.recommendation
                    })
            else:
                for symbol in matching_symbols[:5]:
                    analysis = await self.get_analysis(symbol)
                    if analysis:
                        results.append({
                            "symbol": symbol,
                            "name": symbol,
                            "price": analysis.price,
                            "change_24h": analysis.change_percent,
                            "recommendation": analysis.recommendation
                        })
        
        return results

    async def get_top_coins(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top coins."""
        top_symbols = ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "DOT", "AVAX", "LINK"][:limit]
        
        results = []
        for symbol in top_symbols:
            analysis = await self.get_analysis(symbol)
            if analysis:
                results.append({
                    "symbol": symbol,
                    "name": symbol,
                    "price": analysis.price,
                    "change_24h": analysis.change_percent,
                    "recommendation": analysis.recommendation,
                    "rsi": analysis.rsi
                })
        
        return results

    async def get_high_volume_coins(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get coins sorted by trading volume."""
        all_symbols = list(CRYPTO_SYMBOLS.keys())[:30]
        
        results = []
        for symbol in all_symbols:
            try:
                analysis = await self.get_analysis(symbol)
                if analysis and analysis.volume > 0:
                    results.append({
                        "symbol": symbol,
                        "name": symbol,
                        "price": analysis.price,
                        "change_24h": analysis.change_percent,
                        "volume": analysis.volume,
                        "recommendation": analysis.recommendation,
                        "rsi": analysis.rsi
                    })
            except Exception as e:
                logger.debug(f"Error getting volume for {symbol}: {e}")
                continue
        
        # Sort by volume descending
        results.sort(key=lambda x: x.get("volume", 0), reverse=True)
        
        return results[:limit]

    async def get_death_cross_coins(self, symbols: List[str] = None) -> List[MarketData]:
        """Get coins in death cross (MA50 < MA200)."""
        if symbols is None:
            symbols = list(CRYPTO_SYMBOLS.keys())[:20]
        
        results = []
        for symbol in symbols:
            analysis = await self.get_analysis(symbol)
            if analysis and analysis.is_death_cross:
                results.append(analysis)
        
        return results

    async def get_golden_cross_coins(self, symbols: List[str] = None) -> List[MarketData]:
        """Get coins in golden cross (MA50 > MA200)."""
        if symbols is None:
            symbols = list(CRYPTO_SYMBOLS.keys())[:20]
        
        results = []
        for symbol in symbols:
            analysis = await self.get_analysis(symbol)
            if analysis and analysis.is_golden_cross:
                results.append(analysis)
        
        return results

    async def close(self):
        """Close the service."""
        if self._exchange:
            await self._exchange.close()
            self._exchange = None
        logger.info("MarketDataService closed")


# Global service instance
market_data_service = MarketDataService()

# Alias for backward compatibility with TradingViewService
TradingViewService = MarketDataService
TradingViewData = MarketData
tradingview_service = market_data_service
