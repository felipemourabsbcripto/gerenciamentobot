"""
Price monitoring service using TradingView with Death Cross detection.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from src.config.settings import settings
from src.database import get_async_session, AssetRepository, UserRepository, EntryRepository
from src.services.tradingview_service import TradingViewService
from src.services.technical_analysis import TechnicalAnalysisService

logger = logging.getLogger(__name__)


class PriceMonitor:
    """Monitors cryptocurrency prices and sends alerts using TradingView."""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.tv_service = TradingViewService()
        self.ta_service = TechnicalAnalysisService(self.tv_service)
        # Controle de alertas de reserva - apenas 1x ao dia por usuário
        self._last_reserve_alert: Dict[int, datetime] = {}
        
    async def check_all_assets(self) -> None:
        """Check prices for all tracked assets and send alerts."""
        logger.info("Starting price check for all assets...")
        
        async with get_async_session() as session:
            asset_repo = AssetRepository(session)
            user_repo = UserRepository(session)
            entry_repo = EntryRepository(session)
            
            # Get all unique users with assets
            users = await user_repo.get_all_users()
            
            for user in users:
                try:
                    await self._check_user_assets(
                        user, asset_repo, user_repo, entry_repo
                    )
                    
                    # Check reserve status
                    if user.death_cross_alerts:
                        await self._check_reserve_status(user, asset_repo)
                        
                except Exception as e:
                    logger.error(f"Error checking assets for user {user.telegram_id}: {e}")
                    
        logger.info("Price check completed.")
        
    async def _check_user_assets(
        self,
        user,
        asset_repo: AssetRepository,
        user_repo: UserRepository,
        entry_repo: EntryRepository
    ) -> None:
        """Check all assets for a specific user."""
        if not user.notifications_enabled:
            return
            
        assets = await asset_repo.get_user_assets(user.id)
        
        # Stablecoins não precisam de verificação de preço
        STABLECOINS = {"USDT", "USDC", "BUSD", "DAI", "TUSD"}
        
        for asset in assets:
            if not asset.is_confirmed:
                continue
            
            # Skip stablecoins - preço sempre 1.00, não precisa verificar
            asset_symbol = asset.symbol.upper().replace("USDT", "").replace("/", "")
            if asset_symbol in STABLECOINS or asset.symbol.upper() in STABLECOINS:
                # Apenas atualizar preço como 1.00 sem chamar API
                await asset_repo.update_current_price(asset.id, 1.0)
                continue
                
            try:
                # Get current price from TradingView
                price_data = await self.tv_service.get_price(asset.symbol)
                
                if not price_data:
                    logger.warning(f"Could not get price for {asset.symbol}")
                    continue
                    
                current_price = price_data.get("price", 0)
                
                if current_price <= 0:
                    continue
                    
                # Update asset current price
                await asset_repo.update_current_price(asset.id, current_price)
                
                # Calculate price change
                purchase_price = asset.average_price or asset.purchase_price
                if purchase_price <= 0:
                    continue
                    
                price_change = ((current_price - purchase_price) / purchase_price) * 100
                
                # Check for drop alert (30%)
                if price_change <= -30:
                    await self._send_drop_alert(user, asset, current_price, price_change)
                    
                # Check for profit alert (100%)
                elif price_change >= 100:
                    await self._send_profit_alert(user, asset, current_price, price_change)
                
                # Check for Death Cross
                if user.death_cross_alerts:
                    await self._check_death_cross(user, asset, asset_repo)
                    
            except Exception as e:
                logger.error(f"Error checking asset {asset.symbol}: {e}")
                
    async def _check_death_cross(self, user, asset, asset_repo: AssetRepository) -> None:
        """Check if asset is in Death Cross and send alert."""
        try:
            analysis = await self.ta_service.analyze_asset(asset.symbol)
            
            if not analysis:
                return
                
            # Check if newly in death cross
            if analysis.is_death_cross and not asset.has_death_cross:
                # Update asset status
                await asset_repo.update_death_cross(asset.id, True)
                
                # Check if we already sent an alert recently (within 24h)
                if asset.last_death_cross_alert:
                    time_since_alert = datetime.utcnow() - asset.last_death_cross_alert
                    if time_since_alert < timedelta(hours=24):
                        return
                
                # Send Death Cross alert
                await self._send_death_cross_alert(user, asset, analysis)
                
            elif not analysis.is_death_cross and asset.has_death_cross:
                # Asset recovered from death cross
                await asset_repo.update_death_cross(asset.id, False)
                
        except Exception as e:
            logger.error(f"Error checking death cross for {asset.symbol}: {e}")
            
    async def _check_reserve_status(self, user, asset_repo: AssetRepository) -> None:
        """Check if user's reserve is below target and send alert."""
        try:
            assets = await asset_repo.get_user_assets(user.id)
            
            if not assets:
                return
                
            # Calculate total portfolio value and USDT reserve
            total_value = 0
            usdt_value = 0
            
            for asset in assets:
                if not asset.is_confirmed:
                    continue
                    
                asset_value = asset.quantity * (asset.current_price or asset.purchase_price)
                total_value += asset_value
                
                if asset.symbol.upper() in ["USDT", "USDC", "BUSD", "DAI"]:
                    usdt_value += asset_value
            
            if total_value <= 0:
                return
                
            reserve_percent = (usdt_value / total_value) * 100
            target_percent = user.reserve_target_percent or 15.0
            
            # Alert if reserve is below 50% of target (only once per day)
            if reserve_percent < (target_percent * 0.5):
                # Verificar se já enviou alerta hoje
                last_alert = self._last_reserve_alert.get(user.telegram_id)
                now = datetime.now()
                
                if last_alert is None or (now - last_alert).total_seconds() >= 86400:  # 24 horas
                    await self._send_reserve_alert(user, reserve_percent, target_percent)
                    self._last_reserve_alert[user.telegram_id] = now
                
        except Exception as e:
            logger.error(f"Error checking reserve status: {e}")
            
    async def _send_drop_alert(self, user, asset, current_price: float, change: float) -> None:
        """Send price drop alert."""
        try:
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "📊 Ver Ativo",
                        callback_data=f"asset_detail_{asset.id}"
                    ),
                    InlineKeyboardButton(
                        "➕ Fazer Preço Médio",
                        callback_data=f"add_entry_{asset.id}"
                    )
                ]
            ])
            
            message = (
                f"🔴 **ALERTA DE QUEDA**\n\n"
                f"🪙 **{asset.symbol.upper()}**\n\n"
                f"📉 Queda de **{abs(change):.1f}%**\n"
                f"💰 Preço atual: ${current_price:,.6f}\n"
                f"📊 Preço de compra: ${asset.purchase_price:,.6f}\n\n"
                f"💡 **Sugestão:** Considere fazer preço médio\n"
                f"se acredita no projeto a longo prazo."
            )
            
            await self.bot.send_message(
                chat_id=user.telegram_id,
                text=message,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            
            logger.info(f"Drop alert sent to user {user.telegram_id} for {asset.symbol}")
            
        except Exception as e:
            logger.error(f"Error sending drop alert: {e}")
            
    async def _send_profit_alert(self, user, asset, current_price: float, change: float) -> None:
        """Send profit alert."""
        try:
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "📊 Ver Ativo",
                        callback_data=f"asset_detail_{asset.id}"
                    ),
                    InlineKeyboardButton(
                        "📤 Registrar Venda",
                        callback_data=f"asset_sell_{asset.id}"
                    )
                ]
            ])
            
            message = (
                f"🟢 **ALERTA DE LUCRO**\n\n"
                f"🪙 **{asset.symbol.upper()}**\n\n"
                f"📈 Alta de **{change:.1f}%**\n"
                f"💰 Preço atual: ${current_price:,.6f}\n"
                f"📊 Preço de compra: ${asset.purchase_price:,.6f}\n\n"
                f"💡 **Sugestão:** Considere vender 50%\n"
                f"para realizar lucros e manter exposição."
            )
            
            await self.bot.send_message(
                chat_id=user.telegram_id,
                text=message,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            
            logger.info(f"Profit alert sent to user {user.telegram_id} for {asset.symbol}")
            
        except Exception as e:
            logger.error(f"Error sending profit alert: {e}")
            
    async def _send_death_cross_alert(self, user, asset, analysis) -> None:
        """Send Death Cross alert."""
        try:
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "📊 Análise Completa",
                        callback_data=f"full_analysis_{asset.id}"
                    ),
                    InlineKeyboardButton(
                        "📤 Registrar Venda",
                        callback_data=f"asset_sell_{asset.id}"
                    )
                ]
            ])
            
            rsi_text = f"RSI: {analysis.rsi_14:.1f}" if analysis.rsi_14 else "RSI: N/A"
            
            message = (
                f"☠️ **DEATH CROSS DETECTADO**\n\n"
                f"🪙 **{asset.symbol.upper()}**\n\n"
                f"📉 MA50 cruzou abaixo de MA200\n"
                f"💰 Preço atual: ${analysis.current_price:,.6f}\n"
                f"📊 MA50: ${analysis.ma_50:,.2f}\n"
                f"📊 MA200: ${analysis.ma_200:,.2f}\n"
                f"📈 {rsi_text}\n\n"
                f"⚠️ **Risco:** {analysis.risk_level.upper()}\n"
                f"🎯 **Recomendação TradingView:** {analysis.recommendation}\n\n"
                f"💡 Death Cross é um indicador de tendência de baixa.\n"
                f"Considere reduzir exposição ou definir stop-loss."
            )
            
            await self.bot.send_message(
                chat_id=user.telegram_id,
                text=message,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            
            logger.info(f"Death Cross alert sent to user {user.telegram_id} for {asset.symbol}")
            
        except Exception as e:
            logger.error(f"Error sending death cross alert: {e}")
            
    async def _send_reserve_alert(self, user, current_percent: float, target_percent: float) -> None:
        """Send reserve below target alert."""
        try:
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "💵 Ver Reserva",
                        callback_data="reserve_status"
                    ),
                    InlineKeyboardButton(
                        "➕ Adicionar USDT",
                        callback_data="add_usdt"
                    )
                ]
            ])
            
            message = (
                f"⚠️ **ALERTA DE RESERVA BAIXA**\n\n"
                f"💵 Sua reserva em stablecoins está em **{current_percent:.1f}%**\n"
                f"🎯 Meta configurada: **{target_percent:.1f}%**\n\n"
                f"💡 Manter uma reserva saudável ajuda a:\n"
                f"• Aproveitar oportunidades de compra\n"
                f"• Reduzir risco em quedas\n"
                f"• Manter liquidez para emergências"
            )
            
            await self.bot.send_message(
                chat_id=user.telegram_id,
                text=message,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            
            logger.info(f"Reserve alert sent to user {user.telegram_id}")
            
        except Exception as e:
            logger.error(f"Error sending reserve alert: {e}")
            
    async def close(self) -> None:
        """Close the price monitor and its services."""
        try:
            # Fechar serviço de análise técnica (que fecha seu próprio tv_service se criou)
            await self.ta_service.close()
            
            # Fechar serviço TradingView/MarketData diretamente se temos referência
            if hasattr(self, 'tv_service') and self.tv_service:
                await self.tv_service.close()
                
        except Exception as e:
            logger.error(f"Erro ao fechar PriceMonitor: {e}")
        finally:
            logger.info("PriceMonitor closed")

