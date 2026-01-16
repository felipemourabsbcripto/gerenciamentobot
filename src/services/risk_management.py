"""
Risk Management Service for Futures Trading.
Implements isolated margin risk calculations and liquidity zone detection.
"""
import numpy as np
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RiskCalculation:
    """Risk calculation result."""
    futures_balance: float          # Saldo da carteira de futuros
    risk_percent: float             # % de risco configurado
    max_risk_usd: float             # Risco máximo em USDT
    used_risk_usd: float            # Risco já usado em posições abertas
    available_risk_usd: float       # Risco disponível para novas operações
    suggested_stop_percent: float   # Stop % sugerido baseado na alavancagem
    suggested_stop_price: float     # Preço do stop sugerido
    liquidation_price: float        # Preço de liquidação


@dataclass
class StopLossCalculation:
    """Stop loss calculation based on user input."""
    stop_percent: float             # % de stop escolhido
    risk_usd: float                 # Risco em USDT
    stop_price: float               # Preço do stop
    remaining_risk_usd: float       # Risco restante disponível
    risk_used_percent: float        # % do risco máximo usado


@dataclass
class LiquidityZone:
    """Detected liquidity zone."""
    price: float                    # Preço da zona
    zone_type: str                  # 'support' ou 'resistance'
    strength: str                   # 'weak', 'medium', 'strong'
    distance_percent: float         # Distância do preço atual em %


class RiskManagementService:
    """Service for futures risk management calculations."""
    
    DEFAULT_RISK_PERCENT = 5.0  # 5% default
    MIN_RISK_PERCENT = 0.5
    MAX_RISK_PERCENT = 20.0
    MMR = 0.005  # Maintenance Margin Rate (0.5%)
    
    def __init__(self):
        logger.info("RiskManagementService initialized")
    
    def calculate_risk(
        self,
        futures_balance: float,
        risk_percent: float,
        entry_price: float,
        leverage: int,
        direction: str,
        open_positions_risk: float = 0.0
    ) -> RiskCalculation:
        """
        Calculate risk parameters for a new trade.
        
        Args:
            futures_balance: Current futures wallet balance in USDT
            risk_percent: Configured risk % per trade
            entry_price: Entry price of the trade
            leverage: Leverage multiplier
            direction: 'long' or 'short'
            open_positions_risk: Total risk from open positions in USDT
        
        Returns:
            RiskCalculation with all parameters
        """
        # Risco máximo configurado
        max_risk_usd = futures_balance * (risk_percent / 100)
        
        # Risco disponível (descontando posições abertas)
        available_risk_usd = max_risk_usd - open_positions_risk
        if available_risk_usd < 0:
            available_risk_usd = 0
        
        # Stop % sugerido baseado no risco e alavancagem
        # Para não perder mais que max_risk_usd com a alavancagem:
        # stop_percent = (max_risk_usd / (entry_price * quantity)) / leverage * 100
        # Simplificando: stop_percent ≈ risk_percent / leverage
        suggested_stop_percent = risk_percent / leverage
        
        # Preço do stop sugerido
        if direction.lower() == 'long':
            suggested_stop_price = entry_price * (1 - suggested_stop_percent / 100)
        else:
            suggested_stop_price = entry_price * (1 + suggested_stop_percent / 100)
        
        # Preço de liquidação (usando fórmula de margem isolada)
        # Para posição que arrisca max_risk_usd com leverage x
        margin = max_risk_usd  # Margem = risco máximo
        quantity = (margin * leverage) / entry_price
        notional = entry_price * quantity
        maintenance_margin = notional * self.MMR
        sustainable_margin = margin - maintenance_margin
        
        if sustainable_margin > 0:
            price_adjust = sustainable_margin / quantity
            if direction.lower() == 'long':
                liquidation_price = entry_price - price_adjust
            else:
                liquidation_price = entry_price + price_adjust
        else:
            liquidation_price = entry_price
        
        return RiskCalculation(
            futures_balance=futures_balance,
            risk_percent=risk_percent,
            max_risk_usd=round(max_risk_usd, 2),
            used_risk_usd=round(open_positions_risk, 2),
            available_risk_usd=round(available_risk_usd, 2),
            suggested_stop_percent=round(suggested_stop_percent, 2),
            suggested_stop_price=round(suggested_stop_price, 2),
            liquidation_price=round(liquidation_price, 2)
        )
    
    def calculate_stop_loss(
        self,
        entry_price: float,
        stop_percent: float,
        direction: str,
        leverage: int,
        margin: float,
        max_risk_usd: float,
        available_risk_usd: float
    ) -> StopLossCalculation:
        """
        Calculate stop loss based on user's chosen percentage and trade margin.
        
        Args:
            entry_price: Entry price
            stop_percent: User's chosen stop % (distance from entry)
            direction: 'long' or 'short'
            leverage: Leverage
            margin: Trade margin (collateral/aporte)
            max_risk_usd: Max configured risk per trade
            available_risk_usd: Available risk
        
        Returns:
            StopLossCalculation with details
        """
        # Cálculo correto do risco:
        # A margem é o aporte do trade (colateral)
        # O valor da posição = margin * leverage
        # Se o preço move stop_percent%, a perda = (stop_percent/100) * position_value
        # Portanto: risk_usd = margin * leverage * (stop_percent / 100)
        position_value = margin * leverage
        effective_risk_usd = position_value * (stop_percent / 100)
        
        # Limitar ao risco máximo configurado
        if effective_risk_usd > max_risk_usd:
            effective_risk_usd = max_risk_usd
        
        # Calcular preço do stop
        if direction.lower() == 'long':
            stop_price = entry_price * (1 - stop_percent / 100)
        else:
            stop_price = entry_price * (1 + stop_percent / 100)
        
        # Risco restante
        remaining_risk = available_risk_usd - effective_risk_usd
        if remaining_risk < 0:
            remaining_risk = 0
        
        # % do risco máximo usado
        risk_used_percent = (effective_risk_usd / max_risk_usd * 100) if max_risk_usd > 0 else 0
        
        return StopLossCalculation(
            stop_percent=round(stop_percent, 2),
            risk_usd=round(effective_risk_usd, 2),
            stop_price=round(stop_price, 2),
            remaining_risk_usd=round(remaining_risk, 2),
            risk_used_percent=round(risk_used_percent, 1)
        )
    
    def calculate_stop_percent(
        self,
        entry_price: float,
        stop_price: float,
        direction: str
    ) -> float:
        """
        Calculate stop loss percentage based on entry and stop prices.
        
        Args:
            entry_price: Entry price of the trade
            stop_price: Stop loss price
            direction: 'long' or 'short'
        
        Returns:
            Stop loss percentage (positive value)
        """
        if entry_price <= 0:
            return 0.0
        
        if direction.lower() == 'long':
            # Para long, stop está abaixo do entry
            stop_pct = ((entry_price - stop_price) / entry_price) * 100
        else:
            # Para short, stop está acima do entry
            stop_pct = ((stop_price - entry_price) / entry_price) * 100
        
        return abs(stop_pct)
    
    def calculate_position_size(
        self,
        futures_balance: float,
        risk_percent: float,
        entry_price: float,
        stop_price: float,
        leverage: int
    ) -> Tuple[float, float, float]:
        """
        Calculate optimal position size based on risk.
        
        Returns:
            Tuple of (quantity, margin_required, position_value)
        """
        # Risco máximo em USDT
        max_risk = futures_balance * (risk_percent / 100)
        
        # Distância do stop em %
        stop_distance = abs(entry_price - stop_price) / entry_price
        
        # Com alavancagem, a perda real = stop_distance * leverage * position_value
        # Para limitar a perda a max_risk:
        # max_risk = stop_distance * leverage * margin * leverage = stop_distance * margin * leverage^2
        # Então: margin = max_risk / (stop_distance * leverage)
        
        if stop_distance > 0:
            margin_required = max_risk / (stop_distance * leverage)
        else:
            margin_required = max_risk
        
        # Limitar à margem disponível
        if margin_required > futures_balance:
            margin_required = futures_balance
        
        position_value = margin_required * leverage
        quantity = position_value / entry_price
        
        return (
            round(quantity, 6),
            round(margin_required, 2),
            round(position_value, 2)
        )
    
    def validate_new_trade(
        self,
        futures_balance: float,
        risk_percent: float,
        proposed_risk: float,
        open_positions_risk: float
    ) -> Tuple[bool, str]:
        """
        Validate if a new trade can be opened based on risk limits.
        
        Returns:
            Tuple of (is_valid, message)
        """
        max_risk = futures_balance * (risk_percent / 100)
        used_risk = open_positions_risk
        available_risk = max_risk - used_risk
        
        if proposed_risk > available_risk:
            return (
                False,
                f"❌ Risco insuficiente!\n\n"
                f"• Risco proposto: ${proposed_risk:,.2f}\n"
                f"• Disponível: ${available_risk:,.2f}\n"
                f"• Já usado: ${used_risk:,.2f} de ${max_risk:,.2f}\n\n"
                f"Reduza o tamanho da posição ou feche outras operações."
            )
        
        if proposed_risk > max_risk:
            return (
                False,
                f"❌ Risco excede o limite!\n\n"
                f"• Risco proposto: ${proposed_risk:,.2f}\n"
                f"• Máximo permitido: ${max_risk:,.2f} ({risk_percent}%)\n\n"
                f"Ajuste o stop-loss ou reduza a posição."
            )
        
        return (True, "✅ Trade dentro dos limites de risco")
    
    def format_risk_summary(
        self,
        calculation: RiskCalculation,
        entry_price: float,
        leverage: int,
        direction: str
    ) -> str:
        """Format risk calculation as a readable message."""
        direction_emoji = "🟢 LONG" if direction.lower() == "long" else "🔴 SHORT"
        
        return (
            f"📊 **Análise de Risco**\n\n"
            f"💰 **Carteira de Futuros:** ${calculation.futures_balance:,.2f}\n"
            f"⚙️ **Risco configurado:** {calculation.risk_percent}%\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📈 **Trade:** {direction_emoji} @ ${entry_price:,.2f}\n"
            f"🔧 **Alavancagem:** {leverage}x\n\n"
            f"💵 **Risco máximo sugerido:** ${calculation.max_risk_usd:,.2f}\n"
            f"🔒 **Risco já utilizado:** ${calculation.used_risk_usd:,.2f}\n"
            f"✅ **Disponível para este trade:** ${calculation.available_risk_usd:,.2f}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎯 **Stop sugerido:** ~{calculation.suggested_stop_percent}%\n"
            f"💲 **Preço do stop:** ${calculation.suggested_stop_price:,.2f}\n"
            f"☠️ **Liquidação em:** ${calculation.liquidation_price:,.2f}\n\n"
            f"_Com {leverage}x, um stop de {calculation.suggested_stop_percent}% "
            f"representa ${calculation.max_risk_usd:,.2f} de risco._"
        )
    
    def format_stop_choice(
        self,
        calc: StopLossCalculation,
        max_risk_usd: float
    ) -> str:
        """Format stop loss choice message."""
        remaining_msg = ""
        if calc.remaining_risk_usd > 0:
            remaining_msg = (
                f"\n\n💡 Você usou apenas ${calc.risk_usd:,.2f} de risco "
                f"({calc.risk_used_percent:.0f}% do sugerido).\n"
                f"Sobram **${calc.remaining_risk_usd:,.2f}** para outras operações."
            )
        
        return (
            f"✅ **Stop Definido**\n\n"
            f"📍 **Stop-loss:** {calc.stop_percent}%\n"
            f"💲 **Preço do stop:** ${calc.stop_price:,.2f}\n"
            f"💸 **Risco neste trade:** ${calc.risk_usd:,.2f}"
            f"{remaining_msg}"
        )


class LiquidityZoneService:
    """Service for detecting liquidity zones using price action analysis."""
    
    def __init__(self):
        logger.info("LiquidityZoneService initialized")
    
    def find_swing_points(
        self,
        highs: List[float],
        lows: List[float],
        order: int = 5
    ) -> Tuple[List[int], List[int]]:
        """
        Find swing high and swing low indices.
        
        Args:
            highs: List of high prices
            lows: List of low prices
            order: Number of candles to look on each side
        
        Returns:
            Tuple of (swing_high_indices, swing_low_indices)
        """
        highs_arr = np.array(highs)
        lows_arr = np.array(lows)
        
        swing_highs = []
        swing_lows = []
        
        for i in range(order, len(highs_arr) - order):
            # Check for swing high
            if all(highs_arr[i] >= highs_arr[i-order:i]) and all(highs_arr[i] >= highs_arr[i+1:i+order+1]):
                swing_highs.append(i)
            
            # Check for swing low
            if all(lows_arr[i] <= lows_arr[i-order:i]) and all(lows_arr[i] <= lows_arr[i+1:i+order+1]):
                swing_lows.append(i)
        
        return swing_highs, swing_lows
    
    def group_levels(
        self,
        prices: List[float],
        tolerance_pct: float = 0.008
    ) -> List[float]:
        """
        Group nearby price levels into zones.
        
        Args:
            prices: List of prices
            tolerance_pct: Tolerance percentage for grouping (0.8% default)
        
        Returns:
            List of zone prices (averaged)
        """
        if not prices:
            return []
        
        prices = sorted(prices)
        zones = []
        current_group = [prices[0]]
        
        for p in prices[1:]:
            if p <= current_group[-1] * (1 + tolerance_pct):
                current_group.append(p)
            else:
                zones.append(np.mean(current_group))
                current_group = [p]
        
        if current_group:
            zones.append(np.mean(current_group))
        
        return zones
    
    def detect_zones(
        self,
        highs: List[float],
        lows: List[float],
        closes: List[float],
        current_price: float,
        order: int = 5,
        num_recent: int = 15
    ) -> Dict[str, List[LiquidityZone]]:
        """
        Detect liquidity zones above and below current price.
        
        Args:
            highs: Historical high prices
            lows: Historical low prices
            closes: Historical close prices
            current_price: Current market price
            order: Swing point order
            num_recent: Number of recent swing points to consider
        
        Returns:
            Dict with 'resistance' and 'support' lists of LiquidityZone
        """
        swing_high_idx, swing_low_idx = self.find_swing_points(highs, lows, order)
        
        # Get recent swing points
        recent_highs = [highs[i] for i in swing_high_idx[-num_recent:]]
        recent_lows = [lows[i] for i in swing_low_idx[-num_recent:]]
        
        # Group into zones
        resistance_zones = self.group_levels(recent_highs)
        support_zones = self.group_levels(recent_lows)
        
        # Convert to LiquidityZone objects
        resistances = []
        for price in resistance_zones:
            if price > current_price:
                distance = (price - current_price) / current_price * 100
                strength = self._calculate_strength(price, recent_highs)
                resistances.append(LiquidityZone(
                    price=round(price, 2),
                    zone_type='resistance',
                    strength=strength,
                    distance_percent=round(distance, 2)
                ))
        
        supports = []
        for price in support_zones:
            if price < current_price:
                distance = (current_price - price) / current_price * 100
                strength = self._calculate_strength(price, recent_lows)
                supports.append(LiquidityZone(
                    price=round(price, 2),
                    zone_type='support',
                    strength=strength,
                    distance_percent=round(distance, 2)
                ))
        
        # Sort by distance
        resistances.sort(key=lambda z: z.distance_percent)
        supports.sort(key=lambda z: z.distance_percent)
        
        return {
            'resistance': resistances[:5],  # Top 5 closest
            'support': supports[:5]
        }
    
    def _calculate_strength(self, zone_price: float, all_prices: List[float], tolerance: float = 0.01) -> str:
        """Calculate zone strength based on how many times it was tested."""
        touches = sum(1 for p in all_prices if abs(p - zone_price) / zone_price <= tolerance)
        
        if touches >= 4:
            return 'strong'
        elif touches >= 2:
            return 'medium'
        return 'weak'
    
    def get_nearest_zone(
        self,
        zones: Dict[str, List[LiquidityZone]],
        direction: str
    ) -> Optional[LiquidityZone]:
        """
        Get the nearest relevant zone for a trade direction.
        
        Args:
            zones: Dict with 'resistance' and 'support' zones
            direction: 'long' or 'short'
        
        Returns:
            Nearest LiquidityZone or None
        """
        if direction.lower() == 'long':
            # For long, look at supports (where stop would be)
            supports = zones.get('support', [])
            return supports[0] if supports else None
        else:
            # For short, look at resistances
            resistances = zones.get('resistance', [])
            return resistances[0] if resistances else None
    
    def format_zone_analysis(
        self,
        zones: Dict[str, List[LiquidityZone]],
        direction: str,
        entry_price: float,
        suggested_stop_price: float,
        suggested_risk: float
    ) -> str:
        """Format liquidity zone analysis message."""
        nearest = self.get_nearest_zone(zones, direction)
        
        if not nearest:
            return (
                "🔍 **Análise de Liquidez**\n\n"
                "❌ Não foram detectadas zonas de liquidez relevantes próximas.\n"
                "Recomenda-se usar o stop do gerenciamento de risco."
            )
        
        strength_emoji = {
            'strong': '🔴 FORTE',
            'medium': '🟡 MÉDIA',
            'weak': '🟢 FRACA'
        }
        
        zone_type = 'Suporte' if direction.lower() == 'long' else 'Resistência'
        
        # Calculate risk if using zone as stop
        zone_distance = abs(entry_price - nearest.price) / entry_price * 100
        
        return (
            f"🔍 **Análise de Liquidez**\n\n"
            f"📍 **Zona detectada:** ${nearest.price:,.2f}\n"
            f"📊 **Tipo:** {zone_type} com liquidez {strength_emoji.get(nearest.strength, '')}\n"
            f"📏 **Distância:** ~{nearest.distance_percent:.1f}% do preço atual\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"**Comparação de Stops:**\n\n"
            f"1️⃣ **Stop do Gerenciamento:**\n"
            f"   • Preço: ${suggested_stop_price:,.2f}\n"
            f"   • Risco: ${suggested_risk:,.2f}\n\n"
            f"2️⃣ **Stop na Zona de {zone_type}:**\n"
            f"   • Preço: ${nearest.price:,.2f}\n"
            f"   • Distância: ~{zone_distance:.1f}%\n\n"
            f"💡 _A zona de {zone_type.lower()} pode oferecer proteção adicional "
            f"por estar em região de alta liquidez._"
        )


# Global instances
risk_service = RiskManagementService()
liquidity_service = LiquidityZoneService()
