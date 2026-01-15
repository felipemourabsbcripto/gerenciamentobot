"""
Technical Analysis service using TradingView data.
"""
from typing import Optional, List
from dataclasses import dataclass

from src.services.tradingview_service import TradingViewService, TradingViewData
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TechnicalAnalysis:
    """Data class for complete technical analysis."""
    symbol: str
    current_price: float
    ma_50: Optional[float]
    ma_200: Optional[float]
    rsi_14: Optional[float]
    is_death_cross: bool
    is_golden_cross: bool
    trend: str  # 'bullish', 'bearish', 'neutral'
    recommendation: str  # TradingView recommendation
    risk_level: str  # 'low', 'medium', 'high', 'critical'
    buy_signals: int
    sell_signals: int
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    adx: Optional[float] = None


class TechnicalAnalysisService:
    """Service for technical analysis of cryptocurrency assets using TradingView."""

    def __init__(self, tv_service: Optional[TradingViewService] = None):
        self.tv = tv_service or TradingViewService()
        self._owns_tv = tv_service is None

    async def close(self):
        """Close the service."""
        if self._owns_tv:
            await self.tv.close()

    async def analyze_asset(self, symbol: str) -> Optional[TechnicalAnalysis]:
        """Get complete technical analysis for an asset."""
        try:
            tv_data = await self.tv.get_analysis(symbol)
            
            if not tv_data:
                logger.warning(f"No TradingView data available for {symbol}")
                return None
            
            # Determine trend
            trend = self._determine_trend(tv_data)
            
            # Determine risk level
            risk_level = self._determine_risk_level(tv_data)
            
            return TechnicalAnalysis(
                symbol=symbol.upper(),
                current_price=tv_data.price,
                ma_50=tv_data.ma_50,
                ma_200=tv_data.ma_200,
                rsi_14=tv_data.rsi,
                is_death_cross=tv_data.is_death_cross,
                is_golden_cross=tv_data.is_golden_cross,
                trend=trend,
                recommendation=tv_data.recommendation,
                risk_level=risk_level,
                buy_signals=tv_data.buy_signals,
                sell_signals=tv_data.sell_signals,
                macd=tv_data.macd,
                macd_signal=tv_data.macd_signal,
                adx=tv_data.adx
            )
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None

    def _determine_trend(self, data: TradingViewData) -> str:
        """Determine the overall trend."""
        if data.recommendation in ["STRONG_BUY", "BUY"]:
            return "bullish"
        elif data.recommendation in ["STRONG_SELL", "SELL"]:
            return "bearish"
        else:
            return "neutral"

    def _determine_risk_level(self, data: TradingViewData) -> str:
        """Determine risk level based on indicators."""
        risk_score = 0
        
        # Death Cross = high risk
        if data.is_death_cross:
            risk_score += 3
        
        # RSI conditions
        if data.rsi:
            if data.rsi > 70:  # Overbought
                risk_score += 2
            elif data.rsi < 30:  # Oversold
                risk_score += 1
        
        # Strong sell signals
        if data.recommendation == "STRONG_SELL":
            risk_score += 3
        elif data.recommendation == "SELL":
            risk_score += 2
        
        # More sell signals than buy
        if data.sell_signals > data.buy_signals:
            risk_score += 1
        
        # Map score to risk level
        if risk_score >= 6:
            return "critical"
        elif risk_score >= 4:
            return "high"
        elif risk_score >= 2:
            return "medium"
        else:
            return "low"

    async def detect_death_cross(self, symbol: str) -> bool:
        """Check if an asset is in death cross."""
        analysis = await self.analyze_asset(symbol)
        return analysis.is_death_cross if analysis else False

    async def detect_golden_cross(self, symbol: str) -> bool:
        """Check if an asset is in golden cross."""
        analysis = await self.analyze_asset(symbol)
        return analysis.is_golden_cross if analysis else False

    async def get_recommendation(self, symbol: str) -> Optional[str]:
        """Get TradingView recommendation for an asset."""
        tv_data = await self.tv.get_analysis(symbol)
        return tv_data.recommendation if tv_data else None

    async def scan_death_cross(self, symbols: List[str]) -> List[TechnicalAnalysis]:
        """Scan multiple symbols for death cross."""
        results = []
        for symbol in symbols:
            analysis = await self.analyze_asset(symbol)
            if analysis and analysis.is_death_cross:
                results.append(analysis)
        return results

    async def scan_golden_cross(self, symbols: List[str]) -> List[TechnicalAnalysis]:
        """Scan multiple symbols for golden cross."""
        results = []
        for symbol in symbols:
            analysis = await self.analyze_asset(symbol)
            if analysis and analysis.is_golden_cross:
                results.append(analysis)
        return results


# Global service instance
technical_analysis_service = TechnicalAnalysisService()
