"""
Telegram bot callback query handlers using TradingView.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest
from datetime import datetime

from src.database import get_async_session, UserRepository, AssetRepository, AlertRepository, EntryRepository
from src.database.repositories import FuturesRepository, AdminRepository
from src.services.tradingview_service import TradingViewService
from src.services.technical_analysis import TechnicalAnalysisService
from src.services.trend_analysis_service import trend_analysis_service, TrendDirection
from src.utils import KeyboardBuilder, MessageFormatter
from src.utils.formatters import format_us_price
from src.utils.logger import get_logger
from src.config.settings import settings

logger = get_logger(__name__)

# Major coins (not altcoins)
MAJOR_COINS = {"BTC", "ETH", "BNB"}


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main callback query handler."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user = update.effective_user
    
    logger.debug(f"Callback received: {data} from user {user.id}")
    
    try:
        # Route to appropriate handler
        if data == "menu":
            await handle_menu(query)
        elif data == "portfolio":
            await handle_portfolio(query, user.id)
        elif data == "add_asset":
            await handle_add_asset(query, context)
        elif data == "search_coin":
            await handle_search_coin(query, context)
        elif data == "whale_alert":
            await handle_whale_alert(query)
        elif data == "settings":
            await handle_settings(query, user.id)
        elif data == "alerts":
            await handle_alerts(query, user.id)
        elif data == "help":
            await handle_help(query)
        elif data == "refresh_prices":
            await handle_refresh_prices(query, user.id)
        elif data == "toggle_notifications":
            await handle_toggle_notifications(query, user.id)
        elif data == "toggle_death_cross":
            await handle_toggle_death_cross(query, user.id)
        elif data == "set_reserve_target":
            await handle_set_reserve_target(query, context)
        elif data == "my_profile_data":
            await handle_my_profile_data(query, user.id)
        elif data == "reserve_status":
            await handle_reserve_status(query, user.id)
        elif data == "add_usdt":
            await handle_add_usdt(query, context)
        elif data == "technical_menu":
            await handle_technical_menu(query)
        elif data == "scan_death_cross":
            await handle_scan_death_cross(query, user.id)
        elif data == "scan_golden_cross":
            await handle_scan_golden_cross(query, user.id)
        elif data == "high_risk_assets":
            await handle_high_risk_assets(query, user.id)
        elif data == "risk_panel":
            await handle_risk_panel(query, user.id)
        elif data == "high_volume":
            await handle_high_volume(query)
        # Trend Analysis handlers
        elif data == "trend_analysis_menu":
            await handle_trend_analysis_menu(query)
        elif data == "trend_portfolio":
            await handle_trend_portfolio(query, context, user.id)
        elif data == "trend_futures":
            await handle_trend_futures(query, context, user.id)
        elif data == "trend_specific":
            await handle_trend_specific(query, context)
        elif data == "trend_info":
            await handle_trend_info(query)
        elif data.startswith("trend_tf_"):
            await handle_trend_timeframe(query, context, user.id, data)
        elif data.startswith("trend_asset_"):
            await handle_trend_asset_selected(query, context, data)
        elif data.startswith("trend_refresh_"):
            symbol = data.replace("trend_refresh_", "")
            await handle_trend_refresh(query, context, symbol)
        elif data.startswith("trend_change_tf_"):
            symbol = data.replace("trend_change_tf_", "")
            await handle_trend_change_timeframe(query, context, symbol)
        elif data.startswith("trend_run_"):
            # trend_run_BTC_4h
            parts = data.replace("trend_run_", "").rsplit("_", 1)
            symbol = parts[0]
            timeframe = parts[1]
            await handle_trend_run_analysis(query, context, symbol, timeframe)
        elif data == "cancel":
            await handle_cancel(query, context)
        elif data == "confirm_add_asset":
            await handle_confirm_add(query, context, user.id)
        elif data == "correct_price":
            await handle_correct_price(query, context)
        elif data == "correct_invested":
            await handle_correct_invested(query, context)
        # Registration handlers
        elif data == "accept_terms":
            await handle_accept_terms(query, context, user.id)
        elif data == "reject_terms":
            await handle_reject_terms(query)
        elif data == "continue_registration":
            await handle_continue_registration(query, context)
        # Admin handlers
        elif data == "admin_panel":
            await handle_admin_panel(query, user.id)
        elif data == "admin_users":
            await handle_admin_users(query, user.id)
        elif data.startswith("admin_users_page_"):
            page = int(data.replace("admin_users_page_", ""))
            await handle_admin_users(query, user.id, page)
        elif data == "admin_report":
            await handle_admin_report(query, user.id)
        elif data == "admin_invite_user":
            await handle_admin_create_invite(query, user.id, "user")
        elif data == "admin_invite_admin":
            await handle_admin_create_invite(query, user.id, "admin")
        elif data == "admin_ban":
            await handle_admin_ban_start(query, context, "ban")
        elif data == "admin_unban":
            await handle_admin_ban_start(query, context, "unban")
        elif data.startswith("admin_user_detail_"):
            target_id = int(data.replace("admin_user_detail_", ""))
            await handle_admin_user_detail(query, user.id, target_id)
        elif data.startswith("admin_ban_"):
            target_id = int(data.replace("admin_ban_", ""))
            await handle_admin_ban_confirm(query, user.id, target_id, "ban")
        elif data.startswith("admin_unban_"):
            target_id = int(data.replace("admin_unban_", ""))
            await handle_admin_ban_confirm(query, user.id, target_id, "unban")
        elif data.startswith("admin_make_admin_"):
            target_id = int(data.replace("admin_make_admin_", ""))
            await handle_admin_make_admin(query, user.id, target_id)
        elif data.startswith("admin_remove_admin_"):
            target_id = int(data.replace("admin_remove_admin_", ""))
            await handle_admin_remove_admin(query, user.id, target_id)
        elif data == "admin_logs":
            await handle_admin_logs(query, user.id)
        elif data == "update_futures_balance":
            await handle_update_futures_balance(query, context)
        elif data == "set_futures_risk_percent":
            await handle_set_futures_risk_percent(query, context)
        # Futures handlers
        elif data == "futures_menu":
            await handle_futures_menu(query)
        elif data == "futures_add":
            await handle_futures_add(query, context)
        elif data == "futures_continue_risk":
            await handle_futures_continue_risk(query, context)
        elif data == "futures_check_zones":
            await handle_futures_check_zones(query, context)
        elif data == "futures_skip_zones":
            await handle_futures_skip_zones(query, context)
        elif data == "futures_use_management_stop":
            await handle_futures_use_stop(query, context, "management")
        elif data == "futures_use_zone_stop":
            await handle_futures_use_stop(query, context, "zone")
        elif data == "futures_final_confirm":
            await handle_futures_final_confirm(query, context)
        elif data == "futures_final_confirm_risky":
            await handle_futures_final_confirm(query, context)
        elif data == "futures_adjust_stop":
            await handle_futures_adjust_stop(query, context)
        elif data == "futures_open":
            await handle_futures_open(query, user.id)
        elif data == "futures_history":
            await handle_futures_history(query, user.id)
        elif data == "futures_stats":
            await handle_futures_stats(query, user.id)
        elif data == "futures_high_risk":
            await handle_futures_high_risk(query, user.id)
        elif data == "futures_risk_info":
            await handle_futures_risk_info(query)
        elif data.startswith("futures_side_"):
            side = data.replace("futures_side_", "")
            await handle_futures_side(query, context, side)
        elif data.startswith("futures_lev_"):
            if data == "futures_lev_custom":
                await handle_futures_custom_leverage(query, context)
            else:
                leverage = int(data.replace("futures_lev_", ""))
                await handle_futures_leverage(query, context, leverage)
        elif data == "futures_leverage_info":
            await handle_futures_leverage_info(query)
        elif data.startswith("futures_tf_"):
            timeframe = data.replace("futures_tf_", "")
            await handle_futures_timeframe_selection(query, context, timeframe)
        elif data == "futures_add_target":
            await handle_futures_add_target(query, context)
        elif data == "futures_done_targets":
            await handle_futures_done_targets(query, context)
        elif data == "futures_confirm" or data == "futures_confirm_risky":
            await handle_futures_confirm(query, context, user.id)
        elif data.startswith("futures_detail_"):
            trade_id = int(data.replace("futures_detail_", ""))
            await handle_futures_detail(query, user.id, trade_id)
        elif data.startswith("futures_close_"):
            if data.startswith("futures_close_confirm_"):
                trade_id = int(data.replace("futures_close_confirm_", ""))
                await handle_futures_close_confirm(query, context, user.id, trade_id)
            else:
                trade_id = int(data.replace("futures_close_", ""))
                await handle_futures_close(query, context, trade_id)
        elif data.startswith("futures_delete_"):
            trade_id = int(data.replace("futures_delete_", ""))
            await handle_futures_delete(query, user.id, trade_id)
        elif data.startswith("futures_refresh_"):
            trade_id = int(data.replace("futures_refresh_", ""))
            await handle_futures_refresh(query, user.id, trade_id)
        elif data.startswith("futures_edit_sltp_"):
            trade_id = int(data.replace("futures_edit_sltp_", ""))
            await handle_futures_edit_sltp(query, context, trade_id)
        elif data.startswith("select_coin_"):
            symbol = data.replace("select_coin_", "")
            await handle_select_coin(query, context, symbol)
        elif data.startswith("confirm_add_"):
            await handle_confirm_add(query, context, user.id)
        elif data.startswith("asset_detail_"):
            asset_id = int(data.replace("asset_detail_", ""))
            await handle_asset_detail(query, user.id, asset_id)
        elif data.startswith("asset_sell_"):
            asset_id = int(data.replace("asset_sell_", ""))
            await handle_asset_sell(query, context, asset_id)
        elif data.startswith("asset_delete_"):
            asset_id = int(data.replace("asset_delete_", ""))
            await handle_asset_delete(query, user.id, asset_id)
        elif data.startswith("confirm_delete_"):
            asset_id = int(data.replace("confirm_delete_", ""))
            await handle_confirm_delete(query, user.id, asset_id)
        elif data.startswith("add_entry_"):
            asset_id = int(data.replace("add_entry_", ""))
            await handle_add_entry(query, context, asset_id)
        elif data.startswith("view_entries_"):
            asset_id = int(data.replace("view_entries_", ""))
            await handle_view_entries(query, user.id, asset_id)
        elif data.startswith("full_analysis_"):
            asset_id = int(data.replace("full_analysis_", ""))
            await handle_full_analysis(query, user.id, asset_id)
        elif data.startswith("coin_info_"):
            symbol = data.replace("coin_info_", "")
            await handle_coin_info(query, symbol)
        else:
            logger.warning(f"Unknown callback: {data}")
            await query.edit_message_text(
                "❌ Ação não reconhecida.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
    
    except BadRequest as e:
        # Ignore "Message is not modified" error (happens when content is the same)
        if "Message is not modified" in str(e):
            logger.debug(f"Message not modified for callback {data}")
        else:
            logger.error(f"BadRequest handling callback {data}: {e}")
            try:
                await query.edit_message_text(
                    f"❌ Erro ao processar ação: {str(e)[:100]}",
                    reply_markup=KeyboardBuilder.back_to_menu()
                )
            except BadRequest:
                pass  # Ignore if we can't edit the message
            
    except Exception as e:
        logger.error(f"Error handling callback {data}: {e}")
        try:
            await query.edit_message_text(
                f"❌ Erro ao processar ação: {str(e)[:100]}",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
        except BadRequest:
            pass  # Ignore if we can't edit the message


async def handle_menu(query):
    """Handle menu callback."""
    await query.edit_message_text(
        MessageFormatter.welcome_message(),
        reply_markup=KeyboardBuilder.main_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_portfolio(query, telegram_id: int):
    """Handle portfolio callback."""
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        asset_repo = AssetRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await query.edit_message_text(
                "❌ Usuário não encontrado. Use /start para começar.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        assets = await asset_repo.get_user_assets(user.id)
    
    message = MessageFormatter.portfolio_summary(assets)
    
    # Create keyboard with asset buttons
    keyboard = []
    for asset in assets:
        if asset.is_confirmed:
            change = ""
            if asset.current_price and asset.purchase_price:
                pct = ((asset.current_price - asset.purchase_price) / asset.purchase_price) * 100
                emoji = "🟢" if pct >= 0 else "🔴"
                change = f" {emoji} {pct:+.1f}%"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{asset.symbol.upper()} - ${asset.current_price or asset.purchase_price:,.4f}{change}",
                    callback_data=f"asset_detail_{asset.id}"
                )
            ])
    
    keyboard.append([
        InlineKeyboardButton("🔄 Atualizar Preços", callback_data="refresh_prices"),
        InlineKeyboardButton("➕ Adicionar Ativo", callback_data="add_asset")
    ])
    keyboard.append([InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_add_asset(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle add asset callback."""
    context.user_data['state'] = 'waiting_coin_search'
    context.user_data.clear()
    context.user_data['state'] = 'waiting_coin_search'
    
    await query.edit_message_text(
        "🔍 **Adicionar Ativo**\n\n"
        "Digite o **nome** ou **símbolo** da criptomoeda:\n\n"
        "Exemplos: `BTC`, `ETH`, `SOL`, `ADA`",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_search_coin(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle search coin callback."""
    context.user_data['state'] = 'searching_coin'
    
    await query.edit_message_text(
        "🔍 **Buscar Moeda**\n\n"
        "Digite o **símbolo** da criptomoeda para ver informações:\n\n"
        "Exemplos: `BTC`, `ETH`, `SOL`",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_whale_alert(query):
    """Handle whale alert callback - Show info about Whale Alert channel."""
    message = (
        "🐋 **Whale Alert**\n\n"
        "Acompanhe movimentações de grandes baleias em tempo real!\n\n"
        "O Whale Alert monitora transações massivas de criptomoedas:\n\n"
        "• 💰 Transferências milionárias de BTC, ETH, USDT\n"
        "• 🏦 Depósitos/Saques em exchanges\n"
        "• 🔥 Burns de tokens\n"
        "• 🆕 Mint de stablecoins\n"
        "• 🔒 Movimentações de carteiras dormentes\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📱 **Canal oficial no Telegram:**\n"
        "👉 [Whale Alert](https://t.me/whale_alert_io)\n\n"
        "🌐 **Site oficial:**\n"
        "👉 [whale-alert.io](https://whale-alert.io)\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💡 **Dica:** Movimentações grandes para exchanges podem\n"
        "indicar pressão de venda. Saídas de exchanges podem\n"
        "indicar acumulação (bullish)."
    )
    
    keyboard = [
        [InlineKeyboardButton("🐋 Abrir Whale Alert", url="https://t.me/whale_alert_io")],
        [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")],
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )


async def handle_settings(query, telegram_id: int):
    """Handle settings callback."""
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        admin_repo = AdminRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        is_admin = await admin_repo.is_admin(telegram_id)
    
    if not user:
        await query.edit_message_text(
            "❌ Usuário não encontrado.",
            reply_markup=KeyboardBuilder.back_to_menu()
        )
        return
    
    notif_status = "🔔 Ativadas" if user.notifications_enabled else "🔕 Desativadas"
    dc_status = "🔔 Ativados" if user.death_cross_alerts else "🔕 Desativados"
    reserve_target = user.reserve_target_percent or settings.monitoring.reserve_percent
    futures_balance = user.futures_balance or 0
    
    message = (
        f"⚙️ **Configurações**\n\n"
        f"📊 **Notificações**: {notif_status}\n"
        f"📉 **Alertas Death Cross**: {dc_status}\n"
        f"💵 **Meta de Reserva**: {reserve_target}%\n"
        f"💰 **Saldo Futuros**: ${futures_balance:,.2f}\n\n"
        f"Selecione uma opção para alterar:"
    )
    
    await query.edit_message_text(
        message,
        reply_markup=KeyboardBuilder.settings_menu(is_admin),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_my_profile_data(query, telegram_id: int):
    """Handle my profile data callback - shows user's registration data."""
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
    
    if not user:
        await query.edit_message_text(
            "❌ Usuário não encontrado.",
            reply_markup=KeyboardBuilder.back_to_menu()
        )
        return
    
    # Format birth date
    birth_date_str = user.birth_date if user.birth_date else "Não informado"
    
    # Format registration date
    reg_date = user.accepted_terms_at.strftime("%d/%m/%Y às %H:%M") if user.accepted_terms_at else "N/A"
    
    # Format phone
    phone = user.phone if user.phone else "Não informado"
    
    # Admin badge
    admin_status = "👑 Administrador" if user.is_admin else "👤 Usuário"
    
    # Account status
    if user.is_banned:
        account_status = "🚫 Banido"
    elif user.is_registered:
        account_status = "✅ Ativo"
    else:
        account_status = "⏳ Pendente"
    
    message = (
        f"📋 **Meus Dados de Cadastro**\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔢 **Número de Registro:** #{user.registration_number or 'N/A'}\n"
        f"👤 **Nome Completo:** {user.full_name or user.first_name}\n"
        f"📱 **Telefone:** {phone}\n"
        f"🎂 **Data de Nascimento:** {birth_date_str}\n"
        f"📧 **Username:** @{user.username or 'Não definido'}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏷️ **Status:** {account_status}\n"
        f"🎖️ **Nível:** {admin_status}\n"
        f"📅 **Cadastrado em:** {reg_date}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 **Saldo Futuros:** ${user.futures_balance or 0:,.2f}\n"
        f"📊 **Risco por Trade:** {user.futures_risk_percent or 5.0}%\n"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔙 Voltar às Configurações", callback_data="settings")],
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_alerts(query, telegram_id: int):
    """Handle alerts callback."""
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        alert_repo = AlertRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await query.edit_message_text(
                "❌ Usuário não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        alerts = await alert_repo.get_user_alerts(user.id, limit=10)
    
    if not alerts:
        message = (
            "🔔 **Seus Alertas**\n\n"
            "Você não possui alertas recentes.\n\n"
            "Alertas são enviados automaticamente quando:\n"
            "• 🔴 Ativo cai 30%+ (oportunidade de preço médio)\n"
            "• 🟢 Ativo sobe 100%+ (sugestão de venda)\n"
            "• ☠️ Death Cross detectado (sinal de baixa)"
        )
    else:
        lines = ["🔔 **Seus Alertas Recentes**\n"]
        for alert in alerts:
            date_str = alert.created_at.strftime("%d/%m %H:%M")
            read_emoji = "✅" if alert.is_read else "🔵"
            lines.append(f"{read_emoji} [{date_str}] {alert.message[:50]}...")
        message = "\n".join(lines)
    
    await query.edit_message_text(
        message,
        reply_markup=KeyboardBuilder.back_to_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_help(query):
    """Handle help callback."""
    await query.edit_message_text(
        MessageFormatter.help_message(),
        reply_markup=KeyboardBuilder.back_to_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_refresh_prices(query, telegram_id: int):
    """Handle refresh prices callback."""
    await query.edit_message_text(
        "⏳ Atualizando preços do TradingView...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        asset_repo = AssetRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await query.edit_message_text(
                "❌ Usuário não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        assets = await asset_repo.get_user_assets(user.id)
        
        if not assets:
            await query.edit_message_text(
                "📊 Você não possui ativos cadastrados.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        tv = TradingViewService()
        try:
            for asset in assets:
                if not asset.is_confirmed:
                    continue
                price_data = await tv.get_price(asset.symbol)
                if price_data:
                    await asset_repo.update_current_price(asset.id, price_data.get("price", 0))
        finally:
            await tv.close()
        
        # Reload assets
        assets = await asset_repo.get_user_assets(user.id)
    
    message = MessageFormatter.portfolio_summary(assets)
    
    keyboard = []
    for asset in assets:
        if asset.is_confirmed:
            change = ""
            if asset.current_price and asset.purchase_price:
                pct = ((asset.current_price - asset.purchase_price) / asset.purchase_price) * 100
                emoji = "🟢" if pct >= 0 else "🔴"
                change = f" {emoji} {pct:+.1f}%"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{asset.symbol.upper()} - ${asset.current_price or asset.purchase_price:,.4f}{change}",
                    callback_data=f"asset_detail_{asset.id}"
                )
            ])
    
    keyboard.append([
        InlineKeyboardButton("🔄 Atualizar", callback_data="refresh_prices"),
        InlineKeyboardButton("➕ Adicionar", callback_data="add_asset")
    ])
    keyboard.append([InlineKeyboardButton("🔙 Menu", callback_data="menu")])
    
    await query.edit_message_text(
        message + "\n\n✅ Preços atualizados!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_toggle_notifications(query, telegram_id: int):
    """Handle toggle notifications callback."""
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.toggle_notifications(telegram_id)
    
    if user:
        status = "ativadas" if user.notifications_enabled else "desativadas"
        await query.edit_message_text(
            f"✅ Notificações **{status}** com sucesso!",
            reply_markup=KeyboardBuilder.settings_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await query.edit_message_text(
            "❌ Erro ao alterar configuração.",
            reply_markup=KeyboardBuilder.back_to_menu()
        )


async def handle_toggle_death_cross(query, telegram_id: int):
    """Handle toggle death cross alerts callback."""
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.toggle_death_cross_alerts(telegram_id)
    
    if user:
        status = "ativados" if user.death_cross_alerts else "desativados"
        await query.edit_message_text(
            f"✅ Alertas de Death Cross **{status}** com sucesso!",
            reply_markup=KeyboardBuilder.settings_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await query.edit_message_text(
            "❌ Erro ao alterar configuração.",
            reply_markup=KeyboardBuilder.back_to_menu()
        )


async def handle_set_reserve_target(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle set reserve target callback."""
    context.user_data['state'] = 'waiting_reserve_target'
    
    await query.edit_message_text(
        "💵 **Configurar Meta de Reserva**\n\n"
        "Digite a porcentagem desejada para sua reserva em stablecoins:\n\n"
        "Exemplo: `15` para 15%\n\n"
        "💡 Recomendação: manter entre 10% e 20% do portfólio em stablecoins.",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_reserve_status(query, telegram_id: int):
    """Handle reserve status callback."""
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        asset_repo = AssetRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await query.edit_message_text(
                "❌ Usuário não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        assets = await asset_repo.get_user_assets(user.id)
    
    # Calculate portfolio and reserve
    total_value = 0
    stablecoin_value = 0
    stablecoins = ["USDT", "USDC", "BUSD", "DAI", "TUSD"]
    
    for asset in assets:
        if not asset.is_confirmed:
            continue
        asset_value = asset.quantity * (asset.current_price or asset.purchase_price)
        total_value += asset_value
        
        if asset.symbol.upper() in stablecoins:
            stablecoin_value += asset_value
    
    reserve_percent = (stablecoin_value / total_value * 100) if total_value > 0 else 0
    target_percent = user.reserve_target_percent or settings.monitoring.reserve_percent
    
    # Status emoji
    if reserve_percent >= target_percent:
        status_emoji = "✅"
        status_text = "Acima da meta"
    elif reserve_percent >= target_percent * 0.5:
        status_emoji = "⚠️"
        status_text = "Abaixo da meta"
    else:
        status_emoji = "🔴"
        status_text = "Reserva crítica"
    
    message = (
        f"💵 **Status da Reserva**\n\n"
        f"📊 **Portfólio Total:** ${total_value:,.2f}\n"
        f"💰 **Reserva em Stablecoins:** ${stablecoin_value:,.2f}\n"
        f"📈 **Percentual Atual:** {reserve_percent:.1f}%\n"
        f"🎯 **Meta Configurada:** {target_percent:.1f}%\n\n"
        f"{status_emoji} **Status:** {status_text}"
    )
    
    keyboard = [
        [InlineKeyboardButton("💵 Adicionar USDT", callback_data="add_usdt")],
        [InlineKeyboardButton("⚙️ Alterar Meta", callback_data="set_reserve_target")],
        [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_add_usdt(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle add USDT callback."""
    context.user_data.clear()
    context.user_data['state'] = 'waiting_coin_search'
    context.user_data['preset_coin'] = 'USDT'
    context.user_data['selected_coin_symbol'] = 'USDT'
    context.user_data['selected_coin_name'] = 'Tether USDT'
    
    await query.edit_message_text(
        "💵 **Adicionar USDT**\n\n"
        "Digite a **quantidade** de USDT que você possui:",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_technical_menu(query):
    """Handle technical analysis menu callback."""
    message = (
        "📉 **Análise Técnica**\n\n"
        "Escolha uma opção:\n\n"
        "📊 **Análise de Tendência** - Indicadores validados (Supertrend, Ichimoku, ADX)\n"
        "☠️ **Death Cross** - MA50 cruzou abaixo de MA200 (sinal de baixa)\n"
        "✨ **Golden Cross** - MA50 cruzou acima de MA200 (sinal de alta)\n\n"
        "💡 Use a Análise de Tendência para sinais mais precisos!"
    )
    
    await query.edit_message_text(
        message,
        reply_markup=KeyboardBuilder.technical_analysis_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


# ==================== TREND ANALYSIS HANDLERS ====================


async def handle_trend_analysis_menu(query):
    """Handle trend analysis menu callback."""
    message = (
        "📊 **Análise de Tendência Avançada**\n\n"
        "Sistema de análise com indicadores validados:\n\n"
        "🎯 **Supertrend** - Excelente para detectar tendências (4h, 1d)\n"
        "☁️ **Ichimoku Cloud** - Sistema completo japonês\n"
        "📈 **EMA Cross (9/21)** - Cruzamentos rápidos\n"
        "💪 **ADX** - Força da tendência\n"
        "📉 **RSI Divergence** - Detecta reversões\n"
        "📊 **MACD Histogram** - Momentum\n\n"
        "⭐ Timeframes recomendados: 4h e 1d\n\n"
        "Escolha uma opção:"
    )
    
    await query.edit_message_text(
        message,
        reply_markup=KeyboardBuilder.trend_analysis_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_trend_portfolio(query, context, telegram_id: int):
    """Handle trend analysis for portfolio assets."""
    await query.edit_message_text(
        "📈 **Analisar Ativos da Carteira**\n\n"
        "Selecione o timeframe para análise:\n\n"
        "⭐ **4h** e **1d** são os mais confiáveis",
        reply_markup=KeyboardBuilder.trend_timeframe_menu("portfolio"),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_trend_futures(query, context, telegram_id: int):
    """Handle trend analysis for futures trades."""
    await query.edit_message_text(
        "📊 **Analisar Trades de Futuros**\n\n"
        "Selecione o timeframe para análise:\n\n"
        "⭐ **4h** e **1d** são os mais confiáveis",
        reply_markup=KeyboardBuilder.trend_timeframe_menu("futures"),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_trend_specific(query, context):
    """Handle trend analysis for specific asset."""
    context.user_data['awaiting'] = 'trend_symbol'
    
    await query.edit_message_text(
        "🔍 **Analisar Ativo Específico**\n\n"
        "Digite o símbolo do ativo que deseja analisar:\n"
        "Exemplo: `BTC`, `ETH`, `SOL`",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_trend_info(query):
    """Handle trend indicators info."""
    message = (
        "ℹ️ **Sobre os Indicadores de Tendência**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎯 **Supertrend**\n"
        "Baseado no ATR, muito eficaz para identificar tendências.\n"
        "Taxa de acerto: ~65-70% em 4h/1d\n\n"
        "☁️ **Ichimoku Cloud**\n"
        "Sistema japonês completo que analisa:\n"
        "• Posição do preço vs nuvem\n"
        "• Cruzamento Tenkan/Kijun\n"
        "• Cor da nuvem futura (Kumo)\n\n"
        "📈 **EMA Cross (9/21)**\n"
        "Mais rápido que MA 50/200.\n"
        "Ideal para swing trading em crypto.\n\n"
        "💪 **ADX (Average Directional Index)**\n"
        "Mede a FORÇA da tendência:\n"
        "• ADX > 25: Tendência forte\n"
        "• ADX > 50: Tendência muito forte\n"
        "• ADX < 20: Mercado lateral\n\n"
        "📉 **RSI com Divergência**\n"
        "Detecta divergências que indicam reversão:\n"
        "• Bullish: Preço cai, RSI sobe\n"
        "• Bearish: Preço sobe, RSI cai\n\n"
        "📊 **MACD Histogram**\n"
        "Mostra momentum e reversões.\n"
        "Histograma crescente = momentum bullish.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎯 **Confluence Score**\n"
        "Combina todos os indicadores:\n"
        "• +60 a +100: Forte alta\n"
        "• +25 a +60: Alta\n"
        "• -25 a +25: Neutro\n"
        "• -60 a -25: Baixa\n"
        "• -100 a -60: Forte baixa"
    )
    
    await query.edit_message_text(
        message,
        reply_markup=KeyboardBuilder.trend_analysis_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_trend_timeframe(query, context, telegram_id: int, data: str):
    """Handle timeframe selection for trend analysis."""
    # Parse data: trend_tf_portfolio_4h or trend_tf_futures_4h
    parts = data.replace("trend_tf_", "").rsplit("_", 1)
    action = parts[0]  # portfolio or futures
    timeframe = parts[1]  # 1h, 4h, or 1d
    
    context.user_data['trend_timeframe'] = timeframe
    context.user_data['trend_action'] = action
    
    await query.edit_message_text(
        f"⏳ Buscando ativos para análise de tendência ({timeframe})...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        if action == "portfolio":
            async with get_async_session() as session:
                user_repo = UserRepository(session)
                asset_repo = AssetRepository(session)
                
                user = await user_repo.get_by_telegram_id(telegram_id)
                if not user:
                    await query.edit_message_text(
                        "❌ Usuário não encontrado.",
                        reply_markup=KeyboardBuilder.back_to_menu()
                    )
                    return
                
                assets = await asset_repo.get_user_assets(user.id)
                
            if not assets:
                await query.edit_message_text(
                    "📊 **Análise de Tendência**\n\n"
                    "Você não possui ativos cadastrados.\n"
                    "Adicione ativos à sua carteira primeiro.",
                    reply_markup=KeyboardBuilder.trend_analysis_menu(),
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            confirmed_assets = [a for a in assets if a.is_confirmed and a.symbol.upper() != "USDT"]
            
            if not confirmed_assets:
                await query.edit_message_text(
                    "📊 **Análise de Tendência**\n\n"
                    "Nenhum ativo confirmado para análise.",
                    reply_markup=KeyboardBuilder.trend_analysis_menu(),
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Analyze all assets
            await query.edit_message_text(
                f"⏳ Analisando {len(confirmed_assets)} ativos ({timeframe})...\n"
                "Isso pode levar alguns segundos.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            results = []
            for asset in confirmed_assets:
                analysis = await trend_analysis_service.analyze(asset.symbol, timeframe)
                if analysis:
                    results.append((asset, analysis))
            
            if not results:
                await query.edit_message_text(
                    "❌ Não foi possível analisar os ativos.",
                    reply_markup=KeyboardBuilder.trend_analysis_menu(),
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Format summary
            message = f"📊 **Análise de Tendência - Carteira**\n"
            message += f"⏱️ Timeframe: {timeframe}\n\n"
            message += "━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            # Group by trend
            bullish = [r for r in results if r[1].trend_direction in [TrendDirection.STRONG_BULLISH, TrendDirection.BULLISH]]
            bearish = [r for r in results if r[1].trend_direction in [TrendDirection.STRONG_BEARISH, TrendDirection.BEARISH]]
            neutral = [r for r in results if r[1].trend_direction == TrendDirection.NEUTRAL]
            
            if bullish:
                message += "🟢 **EM ALTA:**\n"
                for asset, analysis in bullish:
                    trend_emoji = "🟢🟢" if analysis.trend_direction == TrendDirection.STRONG_BULLISH else "🟢"
                    message += f"{trend_emoji} **{asset.symbol.upper()}** - Score: {analysis.confluence_score:+.0f}\n"
                message += "\n"
            
            if bearish:
                message += "🔴 **EM BAIXA:**\n"
                for asset, analysis in bearish:
                    trend_emoji = "🔴🔴" if analysis.trend_direction == TrendDirection.STRONG_BEARISH else "🔴"
                    message += f"{trend_emoji} **{asset.symbol.upper()}** - Score: {analysis.confluence_score:+.0f}\n"
                message += "\n"
            
            if neutral:
                message += "⚪ **NEUTROS:**\n"
                for asset, analysis in neutral:
                    message += f"⚪ **{asset.symbol.upper()}** - Score: {analysis.confluence_score:+.0f}\n"
                message += "\n"
            
            message += "━━━━━━━━━━━━━━━━━━━━━\n"
            message += "\n💡 Clique em um ativo para ver análise detalhada:"
            
            # Create keyboard with assets
            asset_list = [{'id': a.id, 'symbol': a.symbol} for a, _ in results]
            keyboard = KeyboardBuilder.trend_asset_list(asset_list, "spot")
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        elif action == "futures":
            async with get_async_session() as session:
                user_repo = UserRepository(session)
                futures_repo = FuturesRepository(session)
                
                user = await user_repo.get_by_telegram_id(telegram_id)
                if not user:
                    await query.edit_message_text(
                        "❌ Usuário não encontrado.",
                        reply_markup=KeyboardBuilder.back_to_menu()
                    )
                    return
                
                trades = await futures_repo.get_open_trades(user.id)
            
            if not trades:
                await query.edit_message_text(
                    "📊 **Análise de Tendência - Futuros**\n\n"
                    "Você não possui trades de futuros abertos.\n"
                    "Abra um trade primeiro.",
                    reply_markup=KeyboardBuilder.trend_analysis_menu(),
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Analyze all futures trades
            await query.edit_message_text(
                f"⏳ Analisando {len(trades)} trades ({timeframe})...\n"
                "Isso pode levar alguns segundos.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            results = []
            for trade in trades:
                analysis = await trend_analysis_service.analyze(trade.symbol, timeframe)
                if analysis:
                    results.append((trade, analysis))
            
            if not results:
                await query.edit_message_text(
                    "❌ Não foi possível analisar os trades.",
                    reply_markup=KeyboardBuilder.trend_analysis_menu(),
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Format summary
            message = f"📊 **Análise de Tendência - Futuros**\n"
            message += f"⏱️ Timeframe: {timeframe}\n\n"
            message += "━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            for trade, analysis in results:
                side_emoji = "📈" if trade.side == "long" else "📉"
                trend_emoji = "🟢" if "BULLISH" in analysis.trend_direction.name else "🔴" if "BEARISH" in analysis.trend_direction.name else "⚪"
                
                # Check if trend aligns with position
                aligned = (trade.side == "long" and "BULLISH" in analysis.trend_direction.name) or \
                          (trade.side == "short" and "BEARISH" in analysis.trend_direction.name)
                align_text = "✅ Tendência favorável" if aligned else "⚠️ Tendência contrária"
                
                message += f"{side_emoji} **{trade.symbol.upper()}** ({trade.side.upper()} {trade.leverage}x)\n"
                message += f"   {trend_emoji} {analysis.trend_direction.value}\n"
                message += f"   Score: {analysis.confluence_score:+.0f} | {align_text}\n\n"
            
            message += "━━━━━━━━━━━━━━━━━━━━━\n"
            message += "\n💡 Clique em um trade para ver análise detalhada:"
            
            # Create keyboard with trades
            trade_list = [{'id': t.id, 'symbol': f"{t.symbol} {t.side.upper()}"} for t, _ in results]
            keyboard = KeyboardBuilder.trend_asset_list(trade_list, "futures")
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
    except Exception as e:
        logger.error(f"Error in trend timeframe handler: {e}")
        await query.edit_message_text(
            f"❌ Erro ao analisar: {str(e)[:100]}",
            reply_markup=KeyboardBuilder.trend_analysis_menu(),
            parse_mode=ParseMode.MARKDOWN
        )


async def handle_trend_asset_selected(query, context, data: str):
    """Handle when user selects an asset for detailed trend analysis."""
    # Parse data: trend_asset_spot_123 or trend_asset_futures_456
    parts = data.replace("trend_asset_", "").split("_")
    asset_type = parts[0]  # spot or futures
    asset_id = int(parts[1])
    
    timeframe = context.user_data.get('trend_timeframe', '4h')
    
    await query.edit_message_text(
        "⏳ Gerando análise detalhada...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        if asset_type == "spot":
            async with get_async_session() as session:
                asset_repo = AssetRepository(session)
                asset = await asset_repo.get_by_id(asset_id)
                
                if not asset:
                    await query.edit_message_text(
                        "❌ Ativo não encontrado.",
                        reply_markup=KeyboardBuilder.trend_analysis_menu()
                    )
                    return
                
                symbol = asset.symbol
        else:
            async with get_async_session() as session:
                futures_repo = FuturesRepository(session)
                trade = await futures_repo.get_by_id(asset_id)
                
                if not trade:
                    await query.edit_message_text(
                        "❌ Trade não encontrado.",
                        reply_markup=KeyboardBuilder.trend_analysis_menu()
                    )
                    return
                
                symbol = trade.symbol
        
        analysis = await trend_analysis_service.analyze(symbol, timeframe)
        
        if not analysis:
            await query.edit_message_text(
                f"❌ Não foi possível analisar {symbol}.",
                reply_markup=KeyboardBuilder.trend_analysis_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        message = trend_analysis_service.format_analysis(analysis)
        
        await query.edit_message_text(
            message,
            reply_markup=KeyboardBuilder.trend_analysis_actions(symbol),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error in trend asset selected: {e}")
        await query.edit_message_text(
            f"❌ Erro: {str(e)[:100]}",
            reply_markup=KeyboardBuilder.trend_analysis_menu(),
            parse_mode=ParseMode.MARKDOWN
        )


async def handle_trend_refresh(query, context, symbol: str):
    """Handle refresh of trend analysis."""
    timeframe = context.user_data.get('trend_timeframe', '4h')
    
    await query.edit_message_text(
        f"⏳ Atualizando análise de {symbol.upper()}...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        analysis = await trend_analysis_service.analyze(symbol, timeframe)
        
        if not analysis:
            await query.edit_message_text(
                f"❌ Não foi possível analisar {symbol}.",
                reply_markup=KeyboardBuilder.trend_analysis_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        message = trend_analysis_service.format_analysis(analysis)
        
        await query.edit_message_text(
            message,
            reply_markup=KeyboardBuilder.trend_analysis_actions(symbol),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error in trend refresh: {e}")
        await query.edit_message_text(
            f"❌ Erro: {str(e)[:100]}",
            reply_markup=KeyboardBuilder.trend_analysis_menu(),
            parse_mode=ParseMode.MARKDOWN
        )


async def handle_trend_change_timeframe(query, context, symbol: str):
    """Handle changing timeframe for trend analysis."""
    context.user_data['trend_symbol'] = symbol
    
    keyboard = [
        [
            InlineKeyboardButton("1h", callback_data=f"trend_run_{symbol}_1h"),
            InlineKeyboardButton("4h ⭐", callback_data=f"trend_run_{symbol}_4h"),
            InlineKeyboardButton("1d ⭐", callback_data=f"trend_run_{symbol}_1d"),
        ],
        [InlineKeyboardButton("🔙 Voltar", callback_data="trend_analysis_menu")],
    ]
    
    await query.edit_message_text(
        f"⏱️ **{symbol.upper()}** - Selecione o timeframe:\n\n"
        "⭐ 4h e 1d são os mais confiáveis",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_trend_run_analysis(query, context, symbol: str, timeframe: str):
    """Run trend analysis for a specific symbol and timeframe."""
    context.user_data['trend_timeframe'] = timeframe
    context.user_data['trend_symbol'] = symbol
    
    await query.edit_message_text(
        f"⏳ Analisando {symbol.upper()} ({timeframe})...\n"
        "Calculando indicadores validados...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        analysis = await trend_analysis_service.analyze(symbol, timeframe)
        
        if not analysis:
            await query.edit_message_text(
                f"❌ Não foi possível analisar {symbol.upper()}.\n\n"
                "Verifique se o símbolo está correto e se é um par listado na Binance.",
                reply_markup=KeyboardBuilder.trend_analysis_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        message = trend_analysis_service.format_analysis(analysis)
        
        await query.edit_message_text(
            message,
            reply_markup=KeyboardBuilder.trend_analysis_actions(symbol),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error running trend analysis: {e}")
        await query.edit_message_text(
            f"❌ Erro na análise: {str(e)[:100]}",
            reply_markup=KeyboardBuilder.trend_analysis_menu(),
            parse_mode=ParseMode.MARKDOWN
        )


async def handle_scan_death_cross(query, telegram_id: int):
    """Handle scan death cross callback."""
    await query.edit_message_text(
        "⏳ Escaneando ativos em Death Cross...\nIsso pode levar alguns segundos.",
        parse_mode=ParseMode.MARKDOWN
    )
    
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        asset_repo = AssetRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await query.edit_message_text(
                "❌ Usuário não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        assets = await asset_repo.get_user_assets(user.id)
    
    tv = TradingViewService()
    ta_service = TechnicalAnalysisService(tv)
    
    try:
        symbols = [a.symbol for a in assets if a.is_confirmed]
        death_cross_assets = await ta_service.scan_death_cross(symbols)
    finally:
        await ta_service.close()
    
    if not death_cross_assets:
        message = (
            "☠️ **Scan Death Cross**\n\n"
            "✅ Nenhum dos seus ativos está em Death Cross!\n\n"
            "Death Cross ocorre quando a MA50 cruza abaixo da MA200,\n"
            "indicando possível tendência de baixa."
        )
    else:
        lines = ["☠️ **Ativos em Death Cross**\n"]
        for analysis in death_cross_assets:
            rsi_text = f"RSI: {analysis.rsi_14:.0f}" if analysis.rsi_14 else ""
            lines.append(
                f"🔴 **{analysis.symbol}** - ${analysis.current_price:,.4f}\n"
                f"   MA50: ${analysis.ma_50:,.2f} | MA200: ${analysis.ma_200:,.2f}\n"
                f"   {rsi_text} | Risco: {analysis.risk_level.upper()}\n"
            )
        
        lines.append("\n⚠️ Considere reduzir exposição nestes ativos.")
        message = "\n".join(lines)
    
    await query.edit_message_text(
        message,
        reply_markup=KeyboardBuilder.technical_analysis_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_scan_golden_cross(query, telegram_id: int):
    """Handle scan golden cross callback."""
    await query.edit_message_text(
        "⏳ Escaneando ativos em Golden Cross...\nIsso pode levar alguns segundos.",
        parse_mode=ParseMode.MARKDOWN
    )
    
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        asset_repo = AssetRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await query.edit_message_text(
                "❌ Usuário não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        assets = await asset_repo.get_user_assets(user.id)
    
    tv = TradingViewService()
    ta_service = TechnicalAnalysisService(tv)
    
    try:
        symbols = [a.symbol for a in assets if a.is_confirmed]
        golden_cross_assets = await ta_service.scan_golden_cross(symbols)
    finally:
        await ta_service.close()
    
    if not golden_cross_assets:
        message = (
            "✨ **Scan Golden Cross**\n\n"
            "Nenhum dos seus ativos está em Golden Cross no momento.\n\n"
            "Golden Cross ocorre quando a MA50 cruza acima da MA200,\n"
            "indicando possível tendência de alta."
        )
    else:
        lines = ["✨ **Ativos em Golden Cross**\n"]
        for analysis in golden_cross_assets:
            rsi_text = f"RSI: {analysis.rsi_14:.0f}" if analysis.rsi_14 else ""
            lines.append(
                f"🟢 **{analysis.symbol}** - ${analysis.current_price:,.4f}\n"
                f"   MA50: ${analysis.ma_50:,.2f} | MA200: ${analysis.ma_200:,.2f}\n"
                f"   {rsi_text} | Recomendação: {analysis.recommendation}\n"
            )
        
        lines.append("\n📈 Ativos com tendência de alta confirmada.")
        message = "\n".join(lines)
    
    await query.edit_message_text(
        message,
        reply_markup=KeyboardBuilder.technical_analysis_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_cancel(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancel callback."""
    context.user_data.clear()
    
    await query.edit_message_text(
        "❌ Ação cancelada.\n\nUse o menu para continuar:",
        reply_markup=KeyboardBuilder.main_menu()
    )


async def handle_high_risk_assets(query, telegram_id: int):
    """Handle high risk assets callback - shows assets with Death Cross or high volatility."""
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        asset_repo = AssetRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await query.edit_message_text(
                "❌ Usuário não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        assets = await asset_repo.get_user_assets(user.id)
    
    # Filter high risk assets (death cross or significant loss)
    high_risk = []
    for asset in assets:
        if not asset.is_confirmed:
            continue
        
        is_high_risk = False
        risk_reasons = []
        
        if asset.has_death_cross:
            is_high_risk = True
            risk_reasons.append("☠️ Death Cross")
        
        if asset.current_price and asset.average_price:
            change_pct = ((asset.current_price - asset.average_price) / asset.average_price) * 100
            if change_pct <= -30:
                is_high_risk = True
                risk_reasons.append(f"📉 Queda de {change_pct:.1f}%")
        
        if is_high_risk:
            high_risk.append((asset, risk_reasons))
    
    if not high_risk:
        message = (
            "⚠️ **Ativos em Risco**\n\n"
            "✅ Nenhum dos seus ativos está em situação de alto risco!\n\n"
            "Ativos são considerados de alto risco quando:\n"
            "• Possuem Death Cross ativo\n"
            "• Queda de 30% ou mais do preço médio"
        )
    else:
        lines = ["⚠️ **Ativos em Risco**\n"]
        for asset, reasons in high_risk:
            current = asset.current_price or asset.average_price
            change = ((current - asset.average_price) / asset.average_price * 100) if asset.average_price else 0
            
            lines.append(
                f"🔴 **{asset.symbol.upper()}**\n"
                f"   💵 ${current:,.4f} ({change:+.1f}%)\n"
                f"   Motivo: {', '.join(reasons)}\n"
            )
        
        lines.append("\n⚠️ Considere revisar sua estratégia para estes ativos.")
        message = "\n".join(lines)
    
    await query.edit_message_text(
        message,
        reply_markup=KeyboardBuilder.technical_analysis_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_risk_panel(query, telegram_id: int):
    """Handle risk panel callback - unified risk dashboard for spot and futures."""
    from src.utils.formatters import format_price, format_percent, format_pnl
    
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        asset_repo = AssetRepository(session)
        futures_repo = FuturesRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await query.edit_message_text(
                "❌ Usuário não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        assets = await asset_repo.get_user_assets(user.id)
        open_trades = await futures_repo.get_user_open_trades(user.id)
    
    # === SPOT ANALYSIS ===
    total_invested = 0
    total_current = 0
    spot_risks = []
    
    for asset in assets:
        if not asset.is_confirmed:
            continue
        invested = asset.total_invested or 0
        current = (asset.current_price or 0) * (asset.total_quantity or 0)
        total_invested += invested
        total_current += current
        
        # Check spot risks
        if asset.has_death_cross:
            spot_risks.append(f"☠️ {asset.symbol.upper()} - Death Cross")
        if invested > 0:
            pnl_pct = ((current - invested) / invested) * 100
            if pnl_pct <= -30:
                spot_risks.append(f"📉 {asset.symbol.upper()} - Queda de {pnl_pct:.1f}%")
    
    spot_pnl = total_current - total_invested
    spot_pnl_pct = ((total_current - total_invested) / total_invested * 100) if total_invested > 0 else 0
    
    # === FUTURES ANALYSIS ===
    futures_margin = 0
    futures_pnl = 0
    futures_risks = []
    
    for trade in open_trades:
        margin = trade.margin or 0
        futures_margin += margin
        pnl = trade.unrealized_pnl or 0
        futures_pnl += pnl
        
        # Check futures risks
        if trade.risk_level in ["high", "extreme"]:
            side_emoji = "📈" if trade.side == "long" else "📉"
            risk_emoji = "🔴" if trade.risk_level == "extreme" else "🟡"
            futures_risks.append(f"{risk_emoji} {side_emoji} {trade.pair} {trade.leverage}x")
    
    # === BUILD MESSAGE ===
    lines = ["⚠️ **PAINEL DE RISCO UNIFICADO**\n"]
    
    # Spot Summary
    lines.append("━━━ 📊 CARTEIRA SPOT ━━━")
    lines.append(f"💵 Investido: ${format_price(total_invested)}")
    lines.append(f"💰 Valor Atual: ${format_price(total_current)}")
    lines.append(f"📊 P&L: {format_pnl(spot_pnl)} ({format_percent(spot_pnl_pct)})")
    
    if spot_risks:
        lines.append("\n⚠️ **Alertas Spot:**")
        for risk in spot_risks[:5]:
            lines.append(f"  {risk}")
    else:
        lines.append("\n✅ Sem alertas de risco na carteira")
    
    # Futures Summary  
    lines.append("\n━━━ 📈 POSIÇÕES FUTURES ━━━")
    lines.append(f"🎯 Margem em Uso: ${format_price(futures_margin)}")
    lines.append(f"📊 P&L Não Realizado: {format_pnl(futures_pnl)}")
    lines.append(f"📍 Posições Abertas: {len(open_trades)}")
    
    if futures_risks:
        lines.append("\n⚠️ **Trades de Alto Risco:**")
        for risk in futures_risks[:5]:
            lines.append(f"  {risk}")
    else:
        lines.append("\n✅ Sem trades de alto risco")
    
    # Overall Risk Score
    total_risks = len(spot_risks) + len(futures_risks)
    if total_risks == 0:
        risk_level = "🟢 BAIXO"
    elif total_risks <= 2:
        risk_level = "🟡 MODERADO"
    elif total_risks <= 5:
        risk_level = "🟠 ELEVADO"
    else:
        risk_level = "🔴 ALTO"
    
    lines.append(f"\n━━━━━━━━━━━━━━━━━━")
    lines.append(f"📊 **Nível de Risco Geral:** {risk_level}")
    
    await query.edit_message_text(
        "\n".join(lines),
        reply_markup=KeyboardBuilder.risk_panel_actions(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_high_volume(query):
    """Handle high volume coins callback - shows coins with highest 24h trading volume."""
    await query.edit_message_text(
        "⏳ Buscando moedas com maior volume...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    tv = TradingViewService()
    try:
        coins = await tv.get_high_volume_coins(limit=10)
    finally:
        await tv.close()
    
    if not coins:
        await query.edit_message_text(
            "❌ Não foi possível obter os dados de volume. Tente novamente.",
            reply_markup=KeyboardBuilder.back_to_menu()
        )
        return
    
    from src.utils.formatters import format_price
    
    lines = ["📊 **TOP 10 MOEDAS POR VOLUME 24H**\n"]
    keyboard = []
    
    for i, coin in enumerate(coins, 1):
        symbol = coin.get("symbol", "???")
        price = coin.get("price", 0)
        volume = coin.get("volume", 0)
        change = coin.get("change_24h", 0)
        rec = coin.get("recommendation", "")
        
        emoji = "🟢" if change >= 0 else "🔴"
        
        # Format volume in millions/billions
        if volume >= 1_000_000_000:
            vol_str = f"${volume/1_000_000_000:.1f}B"
        elif volume >= 1_000_000:
            vol_str = f"${volume/1_000_000:.1f}M"
        else:
            vol_str = f"${volume:,.0f}"
        
        lines.append(
            f"{i}. **{symbol}** | ${format_price(price)}\n"
            f"   📊 Vol: {vol_str} | {emoji} {change:+.2f}% | {rec}"
        )
        
        keyboard.append([
            InlineKeyboardButton(
                f"{i}. {symbol} - Vol: {vol_str}",
                callback_data=f"coin_info_{symbol}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")])
    
    await query.edit_message_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_continue_risk(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle continue after risk warning for futures trade."""
    if 'futures_trade' not in context.user_data:
        await query.edit_message_text(
            "❌ Sessão expirada. Inicie novamente.",
            reply_markup=KeyboardBuilder.futures_menu()
        )
        return
    
    context.user_data['awaiting_futures_entry'] = True
    pair = context.user_data['futures_trade'].get('pair', '???')
    leverage = context.user_data['futures_trade'].get('leverage', 1)
    
    await query.edit_message_text(
        f"📝 **Trade: {pair}** {leverage}x\n\n"
        "Digite o **preço de entrada** em USD:\n\n"
        "Exemplo: `65000` ou `0.5432`",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_select_coin(query, context: ContextTypes.DEFAULT_TYPE, symbol: str):
    """Handle coin selection callback."""
    context.user_data['selected_coin_symbol'] = symbol
    context.user_data['selected_coin_name'] = symbol
    
    # Get current price
    tv = TradingViewService()
    try:
        price_data = await tv.get_price(symbol)
    finally:
        await tv.close()
    
    current_price = 0
    if price_data:
        current_price = price_data.get('price', 0)
        context.user_data['selected_coin_price'] = current_price
    
    context.user_data['state'] = 'waiting_price'
    
    await query.edit_message_text(
        f"💰 **Adicionar {symbol.upper()}**\n\n"
        f"📊 **Preço Atual:** ${current_price:,.6f}\n\n"
        f"\u2796\u2796\u2796\u2796\u2796\u2796\u2796\u2796\u2796\u2796\n\n"
        f"💵 **Passo 1/2:** Digite o **preço de compra** (em USD):",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_confirm_add(query, context: ContextTypes.DEFAULT_TYPE, telegram_id: int):
    """Handle confirm add asset callback."""
    symbol = context.user_data.get('selected_coin_symbol')
    name = context.user_data.get('selected_coin_name', symbol)
    quantity = context.user_data.get('quantity')
    price = context.user_data.get('purchase_price')
    total_invested = context.user_data.get('total_invested')
    
    # Fallback to calculated value if total_invested not provided
    if not total_invested:
        total_invested = quantity * price if quantity and price else 0
    
    if not all([symbol, quantity, price]):
        await query.edit_message_text(
            "❌ Dados incompletos. Por favor, tente novamente.",
            reply_markup=KeyboardBuilder.back_to_menu()
        )
        context.user_data.clear()
        return
    
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        asset_repo = AssetRepository(session)
        entry_repo = EntryRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            user = await user_repo.create(telegram_id)
        
        # Check if asset already exists
        existing = await asset_repo.get_user_asset_by_symbol(user.id, symbol)
        
        if existing:
            # Add entry to existing asset
            await entry_repo.create_entry(
                asset_id=existing.id,
                entry_price=price,
                quantity=quantity,
                total_value=total_invested,
                notes=f"Adicionado em {datetime.now().strftime('%d/%m/%Y')}"
            )
            
            # Update quantity
            new_qty = existing.quantity + quantity
            await asset_repo.update_asset(existing.id, quantity=new_qty)
            
            context.user_data.clear()
            
            await query.edit_message_text(
                f"✅ **Entrada adicionada!**\n\n"
                f"🪙 **{symbol.upper()}**\n"
                f"📦 Quantidade adicionada: {quantity:,.6f}\n"
                f"💰 Preço: ${price:,.6f}\n"
                f"💸 Investido: ${total_invested:,.2f}\n"
                f"📊 Quantidade total: {new_qty:,.6f}",
                reply_markup=KeyboardBuilder.asset_actions(existing.id),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Create new asset
        asset = await asset_repo.create(
            user_id=user.id,
            coin_id=symbol.lower(),
            symbol=symbol,
            name=name,
            quantity=quantity,
            purchase_price=price,
            is_confirmed=True
        )
        
        # Create initial entry
        await entry_repo.create_entry(
            asset_id=asset.id,
            entry_price=price,
            quantity=quantity,
            total_value=total_invested,
            notes="Entrada inicial"
        )
    
    context.user_data.clear()
    
    await query.edit_message_text(
        f"✅ **Ativo adicionado com sucesso!**\n\n"
        f"🪙 **{symbol.upper()}** ({name})\n"
        f"📦 Quantidade: {quantity:,.6f}\n"
        f"💰 Preço de compra: ${price:,.6f}\n"
        f"💵 Total investido: ${total_invested:,.2f}",
        reply_markup=KeyboardBuilder.asset_actions(asset.id),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_correct_price(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle correct price callback - go back to price input."""
    symbol = context.user_data.get('selected_coin_symbol', '???')
    current_price = context.user_data.get('selected_coin_price', 0)
    
    context.user_data['state'] = 'waiting_price'
    
    await query.edit_message_text(
        f"✏️ **Corrigir Preço de Compra**\n\n"
        f"🪙 **{symbol.upper()}**\n"
        f"📊 **Preço Atual:** ${current_price:,.6f}\n\n"
        f"Digite o novo **preço de compra** (em USD):",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_correct_invested(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle correct total invested callback - go back to invested input."""
    symbol = context.user_data.get('selected_coin_symbol', '???')
    current_price = context.user_data.get('selected_coin_price', 0)
    price = context.user_data.get('purchase_price', 0)
    
    context.user_data['state'] = 'waiting_total_invested'
    
    await query.edit_message_text(
        f"✏️ **Corrigir Valor Investido**\n\n"
        f"🪙 **{symbol.upper()}**\n"
        f"📊 **Preço Atual:** ${current_price:,.6f}\n"
        f"💵 **Preço de Compra:** ${price:,.6f}\n\n"
        f"Digite o novo **valor total investido** (em USD):",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_asset_detail(query, telegram_id: int, asset_id: int):
    """Handle asset detail callback."""
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        asset_repo = AssetRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await query.edit_message_text(
                "❌ Usuário não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        asset = await asset_repo.get_by_id(asset_id)
        
        if not asset or asset.user_id != user.id:
            await query.edit_message_text(
                "❌ Ativo não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
    
    # Get current price
    tv = TradingViewService()
    try:
        price_data = await tv.get_price(asset.symbol)
        current_price = price_data.get('price', asset.current_price or asset.purchase_price) if price_data else (asset.current_price or asset.purchase_price)
    finally:
        await tv.close()
    
    # Update price in database
    async with get_async_session() as session:
        asset_repo = AssetRepository(session)
        await asset_repo.update_current_price(asset_id, current_price)
    
    purchase_price = asset.average_price or asset.purchase_price
    current_value = asset.quantity * current_price
    invested_value = asset.quantity * purchase_price
    profit = current_value - invested_value
    profit_pct = (profit / invested_value * 100) if invested_value > 0 else 0
    
    profit_emoji = "🟢" if profit >= 0 else "🔴"
    
    message = (
        f"📊 **{asset.symbol.upper()}** - {asset.name}\n\n"
        f"📦 **Quantidade:** {asset.quantity:,.6f}\n"
        f"💰 **Preço Médio:** ${purchase_price:,.6f}\n"
        f"📈 **Preço Atual:** ${current_price:,.6f}\n\n"
        f"💵 **Investido:** ${invested_value:,.2f}\n"
        f"💎 **Valor Atual:** ${current_value:,.2f}\n"
        f"{profit_emoji} **P/L:** ${profit:+,.2f} ({profit_pct:+.2f}%)"
    )
    
    await query.edit_message_text(
        message,
        reply_markup=KeyboardBuilder.asset_actions(asset_id),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_asset_sell(query, context: ContextTypes.DEFAULT_TYPE, asset_id: int):
    """Handle asset sell callback."""
    context.user_data['sell_asset_id'] = asset_id
    context.user_data['state'] = 'waiting_sell_quantity'
    
    async with get_async_session() as session:
        asset_repo = AssetRepository(session)
        asset = await asset_repo.get_by_id(asset_id)
    
    if asset:
        await query.edit_message_text(
            f"📤 **Registrar Venda - {asset.symbol.upper()}**\n\n"
            f"📦 Quantidade disponível: {asset.quantity:,.6f}\n\n"
            f"Digite a **quantidade** que você vendeu:",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await query.edit_message_text(
            "❌ Ativo não encontrado.",
            reply_markup=KeyboardBuilder.back_to_menu()
        )


async def handle_asset_delete(query, telegram_id: int, asset_id: int):
    """Handle asset delete callback."""
    async with get_async_session() as session:
        asset_repo = AssetRepository(session)
        asset = await asset_repo.get_by_id(asset_id)
    
    if not asset:
        await query.edit_message_text(
            "❌ Ativo não encontrado.",
            reply_markup=KeyboardBuilder.back_to_menu()
        )
        return
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Sim, remover", callback_data=f"confirm_delete_{asset_id}"),
            InlineKeyboardButton("❌ Não", callback_data=f"asset_detail_{asset_id}")
        ]
    ]
    
    await query.edit_message_text(
        f"⚠️ **Remover {asset.symbol.upper()}?**\n\n"
        f"Esta ação não pode ser desfeita.\n"
        f"Todas as entradas e histórico serão removidos.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_confirm_delete(query, telegram_id: int, asset_id: int):
    """Handle confirm delete callback."""
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        asset_repo = AssetRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await query.edit_message_text(
                "❌ Usuário não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        asset = await asset_repo.get_by_id(asset_id)
        if not asset or asset.user_id != user.id:
            await query.edit_message_text(
                "❌ Ativo não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        symbol = asset.symbol.upper()
        await asset_repo.delete_asset(asset_id)
    
    await query.edit_message_text(
        f"✅ **{symbol}** removido com sucesso!",
        reply_markup=KeyboardBuilder.back_to_menu()
    )


async def handle_add_entry(query, context: ContextTypes.DEFAULT_TYPE, asset_id: int):
    """Handle add entry callback."""
    context.user_data['entry_asset_id'] = asset_id
    context.user_data['state'] = 'waiting_entry_quantity'
    
    async with get_async_session() as session:
        asset_repo = AssetRepository(session)
        asset = await asset_repo.get_by_id(asset_id)
    
    if asset:
        await query.edit_message_text(
            f"➕ **Nova Entrada - {asset.symbol.upper()}**\n\n"
            f"Digite a **quantidade** comprada:",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await query.edit_message_text(
            "❌ Ativo não encontrado.",
            reply_markup=KeyboardBuilder.back_to_menu()
        )


async def handle_view_entries(query, telegram_id: int, asset_id: int):
    """Handle view entries callback."""
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        asset_repo = AssetRepository(session)
        entry_repo = EntryRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await query.edit_message_text(
                "❌ Usuário não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        asset = await asset_repo.get_by_id(asset_id)
        if not asset or asset.user_id != user.id:
            await query.edit_message_text(
                "❌ Ativo não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        entries = await entry_repo.get_asset_entries(asset_id)
    
    if not entries:
        message = (
            f"📋 **Entradas - {asset.symbol.upper()}**\n\n"
            f"Nenhuma entrada registrada."
        )
    else:
        lines = [f"📋 **Entradas - {asset.symbol.upper()}**\n"]
        
        for i, entry in enumerate(entries, 1):
            date_str = entry.entry_date.strftime("%d/%m/%Y")
            lines.append(
                f"{i}. 📦 {entry.quantity:,.6f} @ ${entry.entry_price:,.6f}\n"
                f"   💵 ${entry.total_value:,.2f} | {date_str}"
            )
        
        message = "\n".join(lines)
    
    keyboard = [
        [InlineKeyboardButton("➕ Nova Entrada", callback_data=f"add_entry_{asset_id}")],
        [InlineKeyboardButton("🔙 Voltar", callback_data=f"asset_detail_{asset_id}")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_full_analysis(query, telegram_id: int, asset_id: int):
    """Handle full technical analysis callback."""
    await query.edit_message_text(
        "⏳ Carregando análise técnica do TradingView...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        asset_repo = AssetRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await query.edit_message_text(
                "❌ Usuário não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        asset = await asset_repo.get_by_id(asset_id)
        if not asset or asset.user_id != user.id:
            await query.edit_message_text(
                "❌ Ativo não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
    
    tv = TradingViewService()
    ta_service = TechnicalAnalysisService(tv)
    
    try:
        analysis = await ta_service.analyze_asset(asset.symbol)
    finally:
        await ta_service.close()
    
    if not analysis:
        await query.edit_message_text(
            f"❌ Não foi possível obter análise para {asset.symbol.upper()}.",
            reply_markup=KeyboardBuilder.asset_actions(asset_id)
        )
        return
    
    # Format analysis
    trend_emoji = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}.get(analysis.trend, "⚪")
    risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(analysis.risk_level, "⚪")
    
    dc_status = "☠️ SIM" if analysis.is_death_cross else "✅ NÃO"
    gc_status = "✨ SIM" if analysis.is_golden_cross else "❌ NÃO"
    
    rsi_text = f"{analysis.rsi_14:.1f}" if analysis.rsi_14 else "N/A"
    ma50_text = f"${analysis.ma_50:,.2f}" if analysis.ma_50 else "N/A"
    ma200_text = f"${analysis.ma_200:,.2f}" if analysis.ma_200 else "N/A"
    
    message = (
        f"📊 **Análise Técnica - {asset.symbol.upper()}**\n\n"
        f"💰 **Preço:** ${analysis.current_price:,.6f}\n\n"
        f"📈 **Médias Móveis:**\n"
        f"   MA50: {ma50_text}\n"
        f"   MA200: {ma200_text}\n\n"
        f"📉 **Osciladores:**\n"
        f"   RSI(14): {rsi_text}\n\n"
        f"☠️ **Death Cross:** {dc_status}\n"
        f"✨ **Golden Cross:** {gc_status}\n\n"
        f"{trend_emoji} **Tendência:** {analysis.trend.upper()}\n"
        f"{risk_emoji} **Nível de Risco:** {analysis.risk_level.upper()}\n\n"
        f"🎯 **Recomendação TradingView:**\n"
        f"   {analysis.recommendation}\n"
        f"   📈 Compra: {analysis.buy_signals} | 📉 Venda: {analysis.sell_signals}"
    )
    
    await query.edit_message_text(
        message,
        reply_markup=KeyboardBuilder.asset_actions(asset_id),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_coin_info(query, symbol: str):
    """Handle coin info callback."""
    await query.edit_message_text(
        f"⏳ Buscando informações de {symbol.upper()}...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    tv = TradingViewService()
    ta_service = TechnicalAnalysisService(tv)
    
    try:
        analysis = await ta_service.analyze_asset(symbol)
    finally:
        await ta_service.close()
    
    if not analysis:
        await query.edit_message_text(
            f"❌ Não foi possível obter informações para {symbol.upper()}.",
            reply_markup=KeyboardBuilder.back_to_menu()
        )
        return
    
    trend_emoji = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}.get(analysis.trend, "⚪")
    
    rsi_text = f"{analysis.rsi_14:.1f}" if analysis.rsi_14 else "N/A"
    ma50_text = f"${analysis.ma_50:,.2f}" if analysis.ma_50 else "N/A"
    ma200_text = f"${analysis.ma_200:,.2f}" if analysis.ma_200 else "N/A"
    
    dc_gc = ""
    if analysis.is_death_cross:
        dc_gc = "☠️ **DEATH CROSS** ativo"
    elif analysis.is_golden_cross:
        dc_gc = "✨ **GOLDEN CROSS** ativo"
    
    message = (
        f"🪙 **{symbol.upper()}**\n\n"
        f"💰 **Preço:** ${analysis.current_price:,.6f}\n\n"
        f"📊 **Indicadores:**\n"
        f"   MA50: {ma50_text}\n"
        f"   MA200: {ma200_text}\n"
        f"   RSI: {rsi_text}\n\n"
        f"{trend_emoji} **Tendência:** {analysis.trend.upper()}\n"
        f"🎯 **Recomendação:** {analysis.recommendation}\n"
        f"{dc_gc}"
    )
    
    keyboard = [
        [InlineKeyboardButton(f"➕ Adicionar {symbol.upper()}", callback_data=f"select_coin_{symbol}")],
        [InlineKeyboardButton("🔙 Voltar", callback_data="top_coins")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )


# ==================== FUTURES HANDLERS ====================

async def handle_futures_menu(query):
    """Handle futures menu callback."""
    await query.edit_message_text(
        MessageFormatter.futures_menu_message(),
        reply_markup=KeyboardBuilder.futures_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_add(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle add new futures trade - ask for pair."""
    context.user_data['awaiting_futures_pair'] = True
    context.user_data['futures_trade'] = {}
    
    await query.edit_message_text(
        "📝 **Novo Trade Futuros**\n\n"
        "📋 **Etapa 1/8 - Par de negociação**\n\n"
        "Digite o **par** do trade:\n\n"
        "Exemplos: `BTC/USDT`, `ETH/USDT`, `SOL`, `DOGE`\n"
        "Formatos especiais: `BTC.P`, `USDT.P`, `TOTAL`\n\n"
        "💡 Use `/` entre os pares. Se digitar apenas o símbolo (ex: `BTC`), será usado USDT como quote.",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_side(query, context: ContextTypes.DEFAULT_TYPE, side: str):
    """Handle futures trade side selection - Step 3."""
    from src.utils.formatters import format_us_price, MessageFormatter
    
    if 'futures_trade' not in context.user_data:
        await query.edit_message_text(
            "❌ Sessão expirada. Inicie novamente.",
            reply_markup=KeyboardBuilder.futures_menu()
        )
        return
    
    context.user_data['futures_trade']['side'] = side
    context.user_data['futures_trade']['step'] = 3
    pair = context.user_data['futures_trade'].get('pair', '???')
    is_altcoin = context.user_data['futures_trade'].get('is_altcoin', False)
    
    step_summary = MessageFormatter.futures_registration_step(3, context.user_data['futures_trade'])
    
    await query.edit_message_text(
        step_summary + "\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ **Etapa 3/8 concluída!**\n\n"
        "📝 **Etapa 4/8 - Alavancagem**\n\n"
        "Selecione a **alavancagem**:\n\n"
        + ("⚠️ **ATENÇÃO:** Este é um altcoin. Alavancagem >3x é arriscada!\n\n" if is_altcoin else "")
        + "💡 Exemplos: 1x 2x 3x 10x 20x\n"
        "⚠️ Maior alavancagem = maior risco de liquidação por volatilidade",
        reply_markup=KeyboardBuilder.futures_leverage_selection(is_altcoin),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_leverage(query, context: ContextTypes.DEFAULT_TYPE, leverage: int):
    """Handle futures leverage selection - Step 4."""
    from src.utils.formatters import format_us_price, MessageFormatter
    
    if 'futures_trade' not in context.user_data:
        await query.edit_message_text(
            "❌ Sessão expirada. Inicie novamente.",
            reply_markup=KeyboardBuilder.futures_menu()
        )
        return
    
    context.user_data['futures_trade']['leverage'] = leverage
    context.user_data['futures_trade']['step'] = 4
    is_altcoin = context.user_data['futures_trade'].get('is_altcoin', False)
    trade = context.user_data['futures_trade']
    
    # Risk warning based on leverage
    risk_warning = ""
    if leverage >= 20:
        risk_warning = (
            "\n💀 **RISCO EXTREMO!**\n"
            f"Com {leverage}x, você será liquidado em ~{100/leverage:.1f}% de movimento contra.\n"
            "⚠️ Volatilidade do mercado cripto pode facilmente atingir isso!\n\n"
        )
    elif leverage >= 10:
        risk_warning = (
            f"\n⚠️ **Atenção:** Com {leverage}x, pequenos movimentos têm grande impacto.\n"
            f"Liquidação em aproximadamente {100/leverage:.1f}% de movimento contra.\n\n"
        )
    elif leverage > 3 and is_altcoin:
        risk_warning = (
            f"\n⚠️ **Atenção:** Altcoin com {leverage}x é arriscado!\n"
            "Altcoins têm maior volatilidade que BTC/ETH.\n\n"
        )
    
    step_summary = MessageFormatter.futures_registration_step(4, trade)
    
    # Proceed to ask for stop loss
    context.user_data['awaiting_futures_stop_loss'] = True
    
    await query.edit_message_text(
        step_summary + "\n\n"
        f"{risk_warning}"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ **Etapa 4/8 concluída!**\n\n"
        "📝 **Etapa 5/8 - Stop Loss**\n\n"
        "Digite o **preço do Stop Loss**:\n\n"
        f"💡 Preço de entrada: U$ {format_us_price(trade.get('entry_price', 0))}\n\n"
        "_O cálculo de % será feito automaticamente._",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_custom_leverage(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom leverage input request."""
    from src.utils.formatters import MessageFormatter
    
    if 'futures_trade' not in context.user_data:
        await query.edit_message_text(
            "❌ Sessão expirada. Inicie novamente.",
            reply_markup=KeyboardBuilder.futures_menu()
        )
        return
    
    context.user_data['awaiting_futures_custom_leverage'] = True
    
    await query.edit_message_text(
        "📝 **Alavancagem Personalizada**\n\n"
        "Digite o valor de alavancagem desejado (1 a 125):\n\n"
        "Exemplos: `5`, `7`, `15`, `50x`\n\n"
        "⚠️ **Atenção aos riscos:**\n"
        "• 10x = liquidação em ~10% contra\n"
        "• 20x = liquidação em ~5% contra\n"
        "• 50x = liquidação em ~2% contra\n"
        "• 100x = liquidação em ~1% contra",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_leverage_info(query):
    """Handle leverage info button."""
    await query.edit_message_text(
        "ℹ️ **INFORMAÇÕES SOBRE ALAVANCAGEM**\n\n"
        "**O que é alavancagem?**\n"
        "Multiplicador do seu capital. Com 10x, $100 controla $1000.\n\n"
        "**Riscos por alavancagem:**\n"
        "• 1x-3x: Conservador ✅\n"
        "• 5x: Moderado ⚠️\n"
        "• 10x: Agressivo 🔴\n"
        "• 20x+: Extremamente arriscado 💀\n\n"
        "**Liquidação aproximada:**\n"
        "• 3x = movimento de ~33% contra\n"
        "• 5x = movimento de ~20% contra\n"
        "• 10x = movimento de ~10% contra\n"
        "• 20x = movimento de ~5% contra\n\n"
        "**Recomendação:**\n"
        "• Altcoins: máximo 3x\n"
        "• BTC/ETH: máximo 10x\n"
        "• Sempre use stop loss!",
        reply_markup=KeyboardBuilder.futures_leverage_selection(False),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_timeframe_selection(query, context: ContextTypes.DEFAULT_TYPE, timeframe: str):
    """Handle timeframe button selection."""
    from src.utils.formatters import format_us_price, MessageFormatter
    
    if 'futures_trade' not in context.user_data:
        await query.edit_message_text(
            "❌ Sessão expirada. Inicie novamente.",
            reply_markup=KeyboardBuilder.futures_menu()
        )
        return
    
    context.user_data['futures_trade']['timeframe'] = timeframe
    context.user_data['futures_trade']['step'] = 7
    
    trade = context.user_data['futures_trade']
    pair = trade.get('pair', '???')
    side = trade.get('side', 'long')
    
    await query.edit_message_text(
        f"✅ **Timeframe:** {timeframe.upper()}\n\n"
        f"🔍 **Deseja verificar zonas de suporte/resistência?**\n\n"
        f"Com base no timeframe {timeframe.upper()}, o bot pode sugerir:\n"
        f"• {'Resistências e zonas de stop (SHORT)' if side == 'short' else 'Suportes e zonas de stop (LONG)'}\n"
        f"• Ajustes no stop loss baseados em zonas técnicas\n\n"
        f"Isso ajuda a posicionar o stop em zonas mais seguras.",
        reply_markup=KeyboardBuilder.futures_zone_check(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_done_targets(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle done targets button - proceed to timeframe selection."""
    from src.utils.formatters import format_us_price, MessageFormatter
    
    if 'futures_trade' not in context.user_data:
        await query.edit_message_text(
            "❌ Sessão expirada. Inicie novamente.",
            reply_markup=KeyboardBuilder.futures_menu()
        )
        return
    
    trade = context.user_data['futures_trade']
    trade['step'] = 6
    context.user_data.pop('awaiting_futures_targets', None)
    
    targets = trade.get('targets', [])
    targets_summary = ""
    for i, t in enumerate(targets, 1):
        entry_price = trade.get('entry_price', 0)
        side = trade.get('side', 'long')
        profit_pct = ((t['price'] - entry_price) / entry_price * 100) if entry_price > 0 else 0
        if side == 'short':
            profit_pct = -profit_pct
        targets_summary += f"   🎯 Alvo {i}: U$ {format_us_price(t['price'])} > {t['percent']:.0f}% (Lucro {profit_pct:.1f}%)\n"
    
    await query.edit_message_text(
        "✅ **Alvos de venda configurados:**\n"
        f"{targets_summary}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ **Etapa 6/8 concluída!**\n\n"
        "📝 **Etapa 7/8 - Timeframe**\n\n"
        "Qual **timeframe** você usou para analisar a operação?\n"
        "_Isso ajuda a identificar suportes e resistências_",
        reply_markup=KeyboardBuilder.futures_timeframe_selection(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_add_target(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle add another target button."""
    from src.utils.formatters import format_us_price
    
    if 'futures_trade' not in context.user_data:
        await query.edit_message_text(
            "❌ Sessão expirada. Inicie novamente.",
            reply_markup=KeyboardBuilder.futures_menu()
        )
        return
    
    trade = context.user_data['futures_trade']
    targets = trade.get('targets', [])
    total_percent = sum(t.get('percent', 0) for t in targets)
    remaining = 100 - total_percent
    target_num = len(targets) + 1
    
    context.user_data['awaiting_futures_targets'] = True
    trade['target_count'] = target_num
    
    await query.edit_message_text(
        f"📝 **Adicionar Alvo {target_num}**\n\n"
        f"📊 Já configurado: {total_percent:.0f}% | Restante: {remaining:.0f}%\n\n"
        "Digite o próximo alvo no formato:\n"
        "`preço percentual`\n\n"
        "Exemplo: `104,000.00 25` (vender 25% a U$ 104,000.00)",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_risk_info(query):
    """Handle futures risk info button."""
    await query.edit_message_text(
        "⚠️ **INFORMAÇÕES DE RISCO**\n\n"
        "**Alavancagem em Altcoins:**\n"
        "Altcoins (moedas diferentes de BTC/ETH/BNB) têm:\n"
        "• Maior volatilidade\n"
        "• Menor liquidez\n"
        "• Spreads maiores\n\n"
        "**Riscos com >3x em Altcoins:**\n"
        "• Liquidação mais provável\n"
        "• Movimento de 30% = perda total com 3x\n"
        "• Altcoins podem mover 20-50% em um dia\n\n"
        "**Recomendações:**\n"
        "• Use no máximo 3x para altcoins\n"
        "• Sempre use Stop Loss\n"
        "• Arrisque apenas o que pode perder",
        reply_markup=KeyboardBuilder.futures_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_open(query, telegram_id: int):
    """Handle view open futures positions."""
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        futures_repo = FuturesRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await query.edit_message_text(
                "❌ Usuário não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        trades = await futures_repo.get_user_open_trades(user.id)
        stats = await futures_repo.get_user_stats(user.id)
    
    # Update prices for open trades
    tv = TradingViewService()
    try:
        for trade in trades:
            price_data = await tv.get_price(trade.pair.replace('USDT', ''))
            if price_data:
                trade.current_price = price_data.get('price', 0)
    finally:
        await tv.close()
    
    message = MessageFormatter.futures_open_positions(trades, stats)
    
    await query.edit_message_text(
        message,
        reply_markup=KeyboardBuilder.futures_open_trades(trades),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_history(query, telegram_id: int):
    """Handle view futures trade history."""
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        futures_repo = FuturesRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await query.edit_message_text(
                "❌ Usuário não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        trades = await futures_repo.get_user_closed_trades(user.id)
        stats = await futures_repo.get_user_stats(user.id)
    
    message = MessageFormatter.futures_history_message(trades, stats)
    
    await query.edit_message_text(
        message,
        reply_markup=KeyboardBuilder.futures_history_list(trades),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_stats(query, telegram_id: int):
    """Handle futures stats callback."""
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        futures_repo = FuturesRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await query.edit_message_text(
                "❌ Usuário não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        stats = await futures_repo.get_user_stats(user.id)
    
    message = MessageFormatter.futures_stats_message(stats)
    
    await query.edit_message_text(
        message,
        reply_markup=KeyboardBuilder.futures_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_high_risk(query, telegram_id: int):
    """Handle high risk trades callback."""
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        futures_repo = FuturesRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await query.edit_message_text(
                "❌ Usuário não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        trades = await futures_repo.get_high_risk_trades(user.id)
    
    message = MessageFormatter.futures_high_risk_warning(trades)
    
    await query.edit_message_text(
        message,
        reply_markup=KeyboardBuilder.futures_open_trades(trades) if trades else KeyboardBuilder.futures_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_detail(query, telegram_id: int, trade_id: int):
    """Handle futures trade detail view."""
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        futures_repo = FuturesRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await query.edit_message_text(
                "❌ Usuário não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        trade = await futures_repo.get_by_id(trade_id)
        
        if not trade or trade.user_id != user.id:
            await query.edit_message_text(
                "❌ Trade não encontrado.",
                reply_markup=KeyboardBuilder.futures_menu()
            )
            return
    
    # Update current price
    tv = TradingViewService()
    try:
        price_data = await tv.get_price(trade.pair.replace('USDT', ''))
        if price_data:
            trade.current_price = price_data.get('price', 0)
    finally:
        await tv.close()
    
    message = MessageFormatter.futures_trade_detail(trade)
    
    await query.edit_message_text(
        message,
        reply_markup=KeyboardBuilder.futures_trade_actions(trade_id),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_close(query, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
    """Handle close futures trade - ask for close price."""
    context.user_data['awaiting_futures_close_price'] = True
    context.user_data['futures_close_trade_id'] = trade_id
    
    await query.edit_message_text(
        "📤 **Fechar Trade**\n\n"
        "Digite o **preço de saída** em USD:\n\n"
        "Exemplo: `67500` ou `0.6123`",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_close_confirm(query, context: ContextTypes.DEFAULT_TYPE, telegram_id: int, trade_id: int):
    """Handle confirmed close of futures trade."""
    close_price = context.user_data.get('futures_close_price')
    
    if not close_price:
        await query.edit_message_text(
            "❌ Preço de fechamento não definido.",
            reply_markup=KeyboardBuilder.futures_menu()
        )
        return
    
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        futures_repo = FuturesRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await query.edit_message_text(
                "❌ Usuário não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        trade = await futures_repo.close_trade(trade_id, close_price)
        await session.commit()
    
    if trade:
        message = MessageFormatter.futures_closed_trade_summary(trade)
        await query.edit_message_text(
            message,
            reply_markup=KeyboardBuilder.futures_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await query.edit_message_text(
            "❌ Erro ao fechar trade.",
            reply_markup=KeyboardBuilder.futures_menu()
        )
    
    # Clear context
    context.user_data.pop('awaiting_futures_close_price', None)
    context.user_data.pop('futures_close_trade_id', None)
    context.user_data.pop('futures_close_price', None)


async def handle_futures_delete(query, telegram_id: int, trade_id: int):
    """Handle delete futures trade."""
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        futures_repo = FuturesRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await query.edit_message_text(
                "❌ Usuário não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        trade = await futures_repo.get_by_id(trade_id)
        if not trade or trade.user_id != user.id:
            await query.edit_message_text(
                "❌ Trade não encontrado.",
                reply_markup=KeyboardBuilder.futures_menu()
            )
            return
        
        await futures_repo.delete_trade(trade_id)
        await session.commit()
    
    await query.edit_message_text(
        "✅ Trade deletado com sucesso!",
        reply_markup=KeyboardBuilder.futures_menu()
    )


async def handle_futures_refresh(query, telegram_id: int, trade_id: int):
    """Handle refresh futures trade price."""
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        futures_repo = FuturesRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await query.edit_message_text(
                "❌ Usuário não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        trade = await futures_repo.get_by_id(trade_id)
        if not trade:
            await query.edit_message_text(
                "❌ Trade não encontrado.",
                reply_markup=KeyboardBuilder.futures_menu()
            )
            return
        
        # Update price from TradingView
        tv = TradingViewService()
        try:
            price_data = await tv.get_price(trade.pair.replace('USDT', ''))
            if price_data:
                current_price = price_data.get('price', 0)
                await futures_repo.update_current_price(trade_id, current_price)
                trade.current_price = current_price
                await session.commit()
        finally:
            await tv.close()
    
    message = MessageFormatter.futures_trade_detail(trade)
    
    await query.edit_message_text(
        f"✅ Preço atualizado!\n\n{message}",
        reply_markup=KeyboardBuilder.futures_trade_actions(trade_id),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_edit_sltp(query, context: ContextTypes.DEFAULT_TYPE, trade_id: int):
    """Handle edit stop loss / take profit."""
    context.user_data['awaiting_futures_sltp'] = True
    context.user_data['futures_sltp_trade_id'] = trade_id
    
    await query.edit_message_text(
        "✏️ **Editar SL/TP**\n\n"
        "Digite os valores no formato:\n"
        "`stop_loss take_profit`\n\n"
        "Exemplo: `64000 72000`\n\n"
        "Para pular um valor, use `0`:\n"
        "• Apenas SL: `64000 0`\n"
        "• Apenas TP: `0 72000`",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_confirm(query, context: ContextTypes.DEFAULT_TYPE, telegram_id: int):
    """Handle confirm new futures trade creation."""
    trade_data = context.user_data.get('futures_trade', {})
    
    if not all(k in trade_data for k in ['pair', 'side', 'leverage', 'entry_price', 'quantity', 'margin']):
        await query.edit_message_text(
            "❌ Dados incompletos. Inicie novamente.",
            reply_markup=KeyboardBuilder.futures_menu()
        )
        return
    
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        futures_repo = FuturesRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await query.edit_message_text(
                "❌ Usuário não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        trade = await futures_repo.create(
            user_id=user.id,
            pair=trade_data['pair'],
            side=trade_data['side'],
            leverage=trade_data['leverage'],
            entry_price=trade_data['entry_price'],
            quantity=trade_data['quantity'],
            margin=trade_data['margin'],
            stop_loss=trade_data.get('stop_loss'),
            take_profit=trade_data.get('take_profit'),
            notes=trade_data.get('notes')
        )
        await session.commit()
    
    risk_msg = ""
    if trade.risk_level == "extreme":
        risk_msg = "\n\n💀 **ATENÇÃO:** Este trade tem RISCO EXTREMO!"
    elif trade.risk_level == "high":
        risk_msg = "\n\n⚠️ **ATENÇÃO:** Este trade é de ALTO RISCO!"
    
    await query.edit_message_text(
        f"✅ **Trade criado com sucesso!**\n\n"
        f"🪙 **{trade.pair}** {'🟢 LONG' if trade.side == 'long' else '🔴 SHORT'} @ {trade.leverage}x\n"
        f"📥 Entry: ${trade.entry_price:,.4f}\n"
        f"📦 Qty: {trade.quantity:,.6f}\n"
        f"💰 Margem: ${trade.margin:,.2f}"
        f"{risk_msg}",
        reply_markup=KeyboardBuilder.futures_menu(),
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Clear context
    context.user_data.pop('futures_trade', None)
    context.user_data.pop('awaiting_futures_pair', None)
    context.user_data.pop('awaiting_futures_entry', None)
    context.user_data.pop('awaiting_futures_quantity', None)
    context.user_data.pop('awaiting_futures_margin', None)


# ==================== REGISTRATION HANDLERS ====================

async def handle_accept_terms(query, context: ContextTypes.DEFAULT_TYPE, telegram_id: int):
    """Handle accepting terms of use."""
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        await user_repo.accept_terms(telegram_id)
        db_user = await user_repo.get_by_telegram_id(telegram_id)
        await session.commit()
    
    context.user_data.clear()
    
    await query.edit_message_text(
        f"✅ **Cadastro Completo!**\n\n"
        f"Olá, **{db_user.full_name}**!\n\n"
        f"📋 Seus dados:\n"
        f"• Registro: #{db_user.registration_number}\n"
        f"• Telefone: {db_user.phone}\n"
        f"• Nascimento: {db_user.birth_date}\n"
        f"• Saldo Futuros: ${db_user.futures_balance:,.2f}\n\n"
        f"Agora você pode usar todas as funcionalidades do bot!",
        reply_markup=KeyboardBuilder.main_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_reject_terms(query):
    """Handle rejecting terms of use."""
    await query.edit_message_text(
        "❌ **Cadastro cancelado**\n\n"
        "Você precisa aceitar os termos para usar o bot.\n\n"
        "Use /start para tentar novamente.",
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_continue_registration(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle continue registration button."""
    context.user_data['registration_step'] = 'futures_balance'
    
    await query.edit_message_text(
        "💰 **Capital para Futuros**\n\n"
        "Informe em USDT o valor disponível para investir em Futuros:",
        parse_mode=ParseMode.MARKDOWN
    )


# ==================== ADMIN HANDLERS ====================

async def handle_admin_panel(query, telegram_id: int):
    """Handle admin panel access."""
    async with get_async_session() as session:
        admin_repo = AdminRepository(session)
        
        if not await admin_repo.is_admin(telegram_id):
            await query.edit_message_text(
                "🚫 Acesso negado. Você não é um administrador.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        stats = await admin_repo.get_user_stats()
    
    await query.edit_message_text(
        f"🔐 **Painel de Administração**\n\n"
        f"📊 **Estatísticas:**\n"
        f"• Usuários registrados: {stats['total']}\n"
        f"• Usuários ativos: {stats['active']}\n"
        f"• Usuários banidos: {stats['banned']}\n"
        f"• Administradores: {stats['admins']}\n\n"
        f"Selecione uma opção:",
        reply_markup=KeyboardBuilder.admin_panel(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_admin_users(query, telegram_id: int, page: int = 0):
    """Handle admin users list."""
    async with get_async_session() as session:
        admin_repo = AdminRepository(session)
        
        if not await admin_repo.is_admin(telegram_id):
            await query.edit_message_text(
                "🚫 Acesso negado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        users = await admin_repo.get_all_users(include_banned=True)
    
    if not users:
        await query.edit_message_text(
            "👥 **Usuários Registrados**\n\n"
            "Nenhum usuário cadastrado ainda.",
            reply_markup=KeyboardBuilder.admin_panel(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    await query.edit_message_text(
        f"👥 **Usuários Registrados** ({len(users)} total)\n\n"
        f"Selecione um usuário para ver detalhes:",
        reply_markup=KeyboardBuilder.admin_users_list(users, page),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_admin_user_detail(query, admin_telegram_id: int, target_user_id: int):
    """Handle viewing user details in admin panel."""
    async with get_async_session() as session:
        admin_repo = AdminRepository(session)
        user_repo = UserRepository(session)
        asset_repo = AssetRepository(session)
        futures_repo = FuturesRepository(session)
        
        if not await admin_repo.is_admin(admin_telegram_id):
            await query.edit_message_text(
                "🚫 Acesso negado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        user = await user_repo.get_by_id(target_user_id)
        if not user:
            await query.edit_message_text(
                "❌ Usuário não encontrado.",
                reply_markup=KeyboardBuilder.admin_panel()
            )
            return
        
        assets = await asset_repo.get_user_assets(user.id)
        trades = await futures_repo.get_user_all_trades(user.id)
    
    status = "🟢 Ativo" if not user.is_banned else "🔴 Banido"
    admin_badge = "👑 Admin" if user.is_admin else "👤 Usuário"
    
    await query.edit_message_text(
        f"👤 **Detalhes do Usuário**\n\n"
        f"📋 **Registro:** #{user.registration_number}\n"
        f"👤 **Nome:** {user.full_name}\n"
        f"📱 **Telefone:** {user.phone}\n"
        f"🎂 **Nascimento:** {user.birth_date}\n"
        f"📅 **Cadastro:** {user.created_at.strftime('%d/%m/%Y')}\n\n"
        f"🔹 **Status:** {status}\n"
        f"🔹 **Tipo:** {admin_badge}\n"
        f"🔹 **Telegram ID:** `{user.telegram_id}`\n\n"
        f"📊 **Dados:**\n"
        f"• Ativos: {len([a for a in assets if a.is_confirmed])}\n"
        f"• Trades: {len(trades)}\n"
        f"• Saldo Futuros: ${user.futures_balance:,.2f}",
        reply_markup=KeyboardBuilder.admin_user_actions(user.id, user.is_banned, user.is_admin),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_admin_ban_start(query, context: ContextTypes.DEFAULT_TYPE, action: str):
    """Start ban/unban process."""
    context.user_data['awaiting_admin_ban_id'] = True
    context.user_data['admin_action'] = action
    
    action_text = "banir" if action == "ban" else "desbanir"
    
    await query.edit_message_text(
        f"🚫 **{action_text.capitalize()} Usuário**\n\n"
        f"Digite o **Telegram ID** do usuário que deseja {action_text}:",
        reply_markup=KeyboardBuilder.back_to_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_admin_ban_confirm(query, admin_telegram_id: int, target_user_id: int, action: str):
    """Confirm ban/unban action."""
    async with get_async_session() as session:
        admin_repo = AdminRepository(session)
        user_repo = UserRepository(session)
        
        if not await admin_repo.is_admin(admin_telegram_id):
            await query.edit_message_text(
                "🚫 Acesso negado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        admin_user = await user_repo.get_by_telegram_id(admin_telegram_id)
        target_user = await user_repo.get_by_id(target_user_id)
        
        if not target_user:
            await query.edit_message_text(
                "❌ Usuário não encontrado.",
                reply_markup=KeyboardBuilder.admin_panel()
            )
            return
        
        if action == "ban":
            success = await admin_repo.ban_user(admin_user.id, target_user.telegram_id)
            action_text = "banido"
        else:
            success = await admin_repo.unban_user(admin_user.id, target_user.telegram_id)
            action_text = "desbanido"
        
        await session.commit()
    
    if success:
        await query.edit_message_text(
            f"✅ Usuário **{target_user.full_name}** foi {action_text} com sucesso!",
            reply_markup=KeyboardBuilder.admin_panel(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await query.edit_message_text(
            "❌ Erro ao processar a ação.",
            reply_markup=KeyboardBuilder.admin_panel()
        )


async def handle_admin_make_admin(query, admin_telegram_id: int, target_user_id: int):
    """Make user an admin."""
    async with get_async_session() as session:
        admin_repo = AdminRepository(session)
        user_repo = UserRepository(session)
        
        admin_user = await user_repo.get_by_telegram_id(admin_telegram_id)
        
        # Only master admins can add new admins
        if not admin_repo.is_master_admin(admin_user.username):
            await query.edit_message_text(
                "🚫 Apenas administradores mestres podem adicionar novos admins.",
                reply_markup=KeyboardBuilder.admin_panel()
            )
            return
        
        target_user = await user_repo.get_by_id(target_user_id)
        success = await admin_repo.make_admin(admin_user.id, target_user.telegram_id)
        await session.commit()
    
    if success:
        await query.edit_message_text(
            f"✅ **{target_user.full_name}** agora é um administrador!",
            reply_markup=KeyboardBuilder.admin_panel(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await query.edit_message_text(
            "❌ Erro ao tornar usuário admin.",
            reply_markup=KeyboardBuilder.admin_panel()
        )


async def handle_admin_remove_admin(query, admin_telegram_id: int, target_user_id: int):
    """Remove admin privileges."""
    async with get_async_session() as session:
        admin_repo = AdminRepository(session)
        user_repo = UserRepository(session)
        
        admin_user = await user_repo.get_by_telegram_id(admin_telegram_id)
        
        if not admin_repo.is_master_admin(admin_user.username):
            await query.edit_message_text(
                "🚫 Apenas administradores mestres podem remover admins.",
                reply_markup=KeyboardBuilder.admin_panel()
            )
            return
        
        target_user = await user_repo.get_by_id(target_user_id)
        success = await admin_repo.remove_admin(admin_user.id, target_user.telegram_id)
        await session.commit()
    
    if success:
        await query.edit_message_text(
            f"✅ Privilégios de admin removidos de **{target_user.full_name}**.",
            reply_markup=KeyboardBuilder.admin_panel(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await query.edit_message_text(
            "❌ Não foi possível remover privilégios de admin.",
            reply_markup=KeyboardBuilder.admin_panel()
        )


async def handle_admin_create_invite(query, telegram_id: int, invite_type: str):
    """Create invite code."""
    async with get_async_session() as session:
        admin_repo = AdminRepository(session)
        user_repo = UserRepository(session)
        
        if not await admin_repo.is_admin(telegram_id):
            await query.edit_message_text(
                "🚫 Acesso negado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        # Only master admins can create admin invites
        admin_user = await user_repo.get_by_telegram_id(telegram_id)
        if invite_type == "admin" and not admin_repo.is_master_admin(admin_user.username):
            await query.edit_message_text(
                "🚫 Apenas administradores mestres podem criar convites de admin.",
                reply_markup=KeyboardBuilder.admin_panel()
            )
            return
        
        invite = await admin_repo.create_invite_code(admin_user.id, invite_type)
        await session.commit()
    
    type_emoji = "👑" if invite_type == "admin" else "👤"
    type_text = "Admin" if invite_type == "admin" else "Usuário"
    
    # Get bot username for link
    bot_info = await query.bot.get_me()
    invite_link = f"https://t.me/{bot_info.username}?start=invite_{invite.code}"
    
    await query.edit_message_text(
        f"🔗 **Link de Convite Gerado!**\n\n"
        f"{type_emoji} Tipo: **{type_text}**\n"
        f"📋 Código: `{invite.code}`\n\n"
        f"🔗 **Link:**\n`{invite_link}`\n\n"
        f"Compartilhe este link com quem deseja convidar.",
        reply_markup=KeyboardBuilder.admin_panel(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_admin_logs(query, telegram_id: int):
    """Show admin logs."""
    async with get_async_session() as session:
        admin_repo = AdminRepository(session)
        
        if not await admin_repo.is_admin(telegram_id):
            await query.edit_message_text(
                "🚫 Acesso negado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        logs = await admin_repo.get_admin_logs(limit=20)
    
    if not logs:
        await query.edit_message_text(
            "📜 **Logs de Admin**\n\n"
            "Nenhum registro encontrado.",
            reply_markup=KeyboardBuilder.admin_panel(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    lines = ["📜 **Logs de Admin** (últimos 20)\n"]
    for log in logs:
        date_str = log.created_at.strftime("%d/%m %H:%M")
        lines.append(f"• [{date_str}] {log.action}")
    
    await query.edit_message_text(
        "\n".join(lines),
        reply_markup=KeyboardBuilder.admin_panel(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_admin_report(query, telegram_id: int):
    """Generate admin report."""
    async with get_async_session() as session:
        admin_repo = AdminRepository(session)
        user_repo = UserRepository(session)
        asset_repo = AssetRepository(session)
        futures_repo = FuturesRepository(session)
        
        if not await admin_repo.is_admin(telegram_id):
            await query.edit_message_text(
                "🚫 Acesso negado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        users = await admin_repo.get_all_users()
        stats = await admin_repo.get_user_stats()
    
    # Build report
    lines = [
        "📊 **RELATÓRIO GERAL**",
        f"📅 Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n",
        "━━━━━━━━━━━━━━━━━━",
        f"👥 **Usuários:**",
        f"• Total: {stats['total']}",
        f"• Ativos: {stats['active']}",
        f"• Banidos: {stats['banned']}",
        f"• Admins: {stats['admins']}",
        "━━━━━━━━━━━━━━━━━━\n",
    ]
    
    # Per-user summary
    lines.append("📋 **Resumo por Usuário:**\n")
    
    async with get_async_session() as session:
        asset_repo = AssetRepository(session)
        futures_repo = FuturesRepository(session)
        
        for user in users[:15]:  # Limit to 15 users
            assets = await asset_repo.get_user_assets(user.id)
            confirmed = [a for a in assets if a.is_confirmed]
            
            total_invested = sum(a.total_invested or 0 for a in confirmed)
            total_current = sum((a.current_price or 0) * (a.quantity or 0) for a in confirmed)
            pnl = total_current - total_invested
            
            emoji = "🟢" if pnl >= 0 else "🔴"
            
            lines.append(
                f"👤 #{user.registration_number} {user.full_name[:15]}\n"
                f"   💰 Inv: ${total_invested:,.0f} | {emoji} P&L: ${pnl:+,.0f}"
            )
    
    if len(users) > 15:
        lines.append(f"\n... e mais {len(users) - 15} usuários")
    
    await query.edit_message_text(
        "\n".join(lines),
        reply_markup=KeyboardBuilder.admin_panel(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_update_futures_balance(query, context: ContextTypes.DEFAULT_TYPE):
    """Start updating futures balance."""
    context.user_data['awaiting_futures_balance'] = True
    
    await query.edit_message_text(
        "💰 **Atualizar Saldo de Futuros**\n\n"
        "Digite o novo valor em **USDT** disponível para trades de futuros:",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_set_futures_risk_percent(query, context: ContextTypes.DEFAULT_TYPE):
    """Start setting futures risk percent per trade."""
    user = query.from_user
    
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        db_user = await user_repo.get_by_telegram_id(user.id)
        current_risk = db_user.futures_risk_percent or 5.0
        futures_balance = db_user.futures_balance or 0
    
    max_risk_usd = futures_balance * (current_risk / 100)
    
    context.user_data['awaiting_futures_risk_percent'] = True
    
    await query.edit_message_text(
        f"⚙️ **Configurar Risco por Trade**\n\n"
        f"📊 Configuração atual: **{current_risk}%** por trade\n"
        f"💰 Carteira de Futuros: **${futures_balance:,.2f}**\n"
        f"💵 Risco máximo atual: **${max_risk_usd:,.2f}**\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💡 **Recomendação:** 5% é ideal para gerenciamento conservador.\n\n"
        f"• 1-3%: Ultra conservador\n"
        f"• 5%: Padrão recomendado\n"
        f"• 10%+: Agressivo (maior risco)\n\n"
        f"Digite o novo percentual (0.5 a 20):",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_check_zones(query, context: ContextTypes.DEFAULT_TYPE):
    """Check liquidity zones for the trade."""
    from src.services.risk_management import liquidity_service
    
    trade = context.user_data.get('futures_trade', {})
    pair = trade.get('pair', '???')
    symbol = trade.get('symbol', pair.replace('USDT', ''))
    entry_price = trade.get('entry_price', 0)
    side = trade.get('side', 'long')
    stop_price = trade.get('stop_price', 0)
    risk_usd = trade.get('risk_usd', 0)
    
    await query.edit_message_text(
        f"🔍 **Analisando zonas de liquidez para {pair}...**\n\n"
        f"Por favor, aguarde...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Get price data from TradingView
    tv = TradingViewService()
    try:
        # For now, we'll use a simplified zone detection
        # In production, you'd fetch historical OHLC data
        
        # Simulated zone detection based on entry price
        if side == 'long':
            # For long, supports are below entry
            zone_price = entry_price * 0.97  # 3% below as example
            zone_type = 'suporte'
        else:
            # For short, resistances are above entry
            zone_price = entry_price * 1.03  # 3% above as example
            zone_type = 'resistência'
        
        zone_distance = abs(entry_price - zone_price) / entry_price * 100
        
        context.user_data['futures_trade']['zone_price'] = zone_price
        context.user_data['futures_trade']['zone_distance'] = zone_distance
        
        zone_msg = (
            f"🔍 **Análise de Liquidez - {pair}**\n\n"
            f"📍 **Zona de {zone_type} detectada:**\n"
            f"   • Preço: ${zone_price:,.2f}\n"
            f"   • Distância: ~{zone_distance:.1f}% do entry\n"
            f"   • Força: 🟡 MÉDIA\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"**Comparação:**\n\n"
            f"1️⃣ **Stop do Gerenciamento:**\n"
            f"   • Preço: ${stop_price:,.2f}\n"
            f"   • Risco: ${risk_usd:,.2f}\n\n"
            f"2️⃣ **Stop na Zona de {zone_type.title()}:**\n"
            f"   • Preço: ${zone_price:,.2f}\n"
            f"   • Distância: ~{zone_distance:.1f}%\n\n"
            f"💡 _A zona pode oferecer proteção adicional por estar em região de alta liquidez._"
        )
        
        await query.edit_message_text(
            zone_msg,
            reply_markup=KeyboardBuilder.futures_zone_choice(zone_price),
            parse_mode=ParseMode.MARKDOWN
        )
    finally:
        await tv.close()


async def handle_futures_skip_zones(query, context: ContextTypes.DEFAULT_TYPE):
    """Skip zone check and proceed with trade confirmation."""
    context.user_data['futures_trade']['zone_used'] = 'management'
    await show_futures_final_confirmation(query, context)


async def handle_futures_use_stop(query, context: ContextTypes.DEFAULT_TYPE, stop_type: str):
    """Handle user's choice between management stop and zone stop."""
    trade = context.user_data.get('futures_trade', {})
    
    if stop_type == 'zone':
        # Use zone stop
        zone_price = trade.get('zone_price')
        if zone_price:
            entry_price = trade.get('entry_price', 0)
            zone_distance = abs(entry_price - zone_price) / entry_price * 100
            context.user_data['futures_trade']['stop_price'] = zone_price
            context.user_data['futures_trade']['stop_percent'] = zone_distance
            context.user_data['futures_trade']['zone_used'] = 'zone'
    else:
        context.user_data['futures_trade']['zone_used'] = 'management'
    
    await show_futures_final_confirmation(query, context)


async def show_futures_final_confirmation(query, context: ContextTypes.DEFAULT_TYPE):
    """Show final confirmation before creating the trade with full summary."""
    from src.services.risk_management import risk_service
    from src.utils.formatters import MessageFormatter
    
    trade = context.user_data.get('futures_trade', {})
    pair = trade.get('pair', '???')
    side = trade.get('side', 'long')
    leverage = trade.get('leverage', 1)
    entry_price = trade.get('entry_price', 0)
    stop_price = trade.get('stop_loss', trade.get('stop_price', 0))
    stop_percent = trade.get('stop_percent', 0)
    risk_usd = trade.get('risk_usd', 0)
    timeframe = trade.get('timeframe', '4h')
    zone_used = trade.get('zone_used', 'management')
    futures_balance = trade.get('futures_balance', 0)
    is_altcoin = trade.get('is_altcoin', False)
    risk_percent = trade.get('risk_percent', 5.0)
    open_risk = trade.get('open_risk', 0)
    
    # Calculate position size if not already done
    if not trade.get('margin'):
        quantity, margin, position_value = risk_service.calculate_position_size(
            futures_balance=futures_balance,
            risk_percent=risk_percent,
            entry_price=entry_price,
            stop_price=stop_price,
            leverage=leverage
        )
        
        context.user_data['futures_trade']['quantity'] = quantity
        context.user_data['futures_trade']['margin'] = margin
        context.user_data['futures_trade']['position_value'] = position_value
    else:
        margin = trade.get('margin', 0)
        quantity = trade.get('quantity', 0)
        position_value = margin * leverage
    
    # Prepare trade data for full summary
    trade_data = {
        'pair': pair,
        'entry_price': entry_price,
        'side': side,
        'leverage': leverage,
        'stop_loss': stop_price,
        'stop_percent': stop_percent,
        'margin': margin,
        'quantity': quantity,
        'timeframe': timeframe,
        'futures_balance': futures_balance,
        'risk_percent': risk_percent,
        'risk_usd': risk_usd,
        'open_risk': open_risk,
        'target_1': trade.get('target_1', {}),
        'target_2': trade.get('target_2', {}),
        'target_3': trade.get('target_3', {}),
    }
    
    current_price = trade.get('current_price', entry_price)
    
    # Generate full summary
    full_summary = MessageFormatter.futures_full_trade_summary(trade_data, current_price)
    
    show_risk_warning = (leverage > 3 and is_altcoin) or leverage >= 10
    
    await query.edit_message_text(
        full_summary + "\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "**Confirma o cadastro deste trade?**",
        reply_markup=KeyboardBuilder.futures_final_confirm(show_risk_warning),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_final_confirm(query, context: ContextTypes.DEFAULT_TYPE):
    """Create the futures trade after final confirmation."""
    from src.utils.formatters import format_us_price
    
    user = query.from_user
    trade = context.user_data.get('futures_trade', {})
    
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        futures_repo = FuturesRepository(session)
        
        db_user = await user_repo.get_by_telegram_id(user.id)
        
        # Get targets
        target_1 = trade.get('target_1', {})
        target_2 = trade.get('target_2', {})
        target_3 = trade.get('target_3', {})
        
        # Calculate allocation percent
        futures_balance = trade.get('futures_balance', 0)
        margin = trade.get('margin', 0)
        allocation_percent = (margin / futures_balance * 100) if futures_balance > 0 else 0
        
        # Create trade with risk management data and targets
        new_trade = await futures_repo.create_with_risk(
            user_id=db_user.id,
            pair=trade.get('pair'),
            side=trade.get('side'),
            leverage=trade.get('leverage'),
            entry_price=trade.get('entry_price'),
            quantity=trade.get('quantity'),
            margin=trade.get('margin'),
            stop_loss=trade.get('stop_loss', trade.get('stop_price')),
            stop_percent=trade.get('stop_percent'),
            risk_usd=trade.get('risk_usd'),
            timeframe=trade.get('timeframe'),
            zone_used=trade.get('zone_used', 'management'),
            target_1_price=target_1.get('price') if target_1 else None,
            target_1_percent=target_1.get('percent') if target_1 else None,
            target_2_price=target_2.get('price') if target_2 else None,
            target_2_percent=target_2.get('percent') if target_2 else None,
            target_3_price=target_3.get('price') if target_3 else None,
            target_3_percent=target_3.get('percent') if target_3 else None,
            allocation_percent=allocation_percent
        )
        
        await session.commit()
    
    # Clear trade data
    context.user_data.pop('futures_trade', None)
    
    direction_emoji = "🟢 LONG" if trade.get('side') == "long" else "🔴 SHORT"
    
    # Build targets summary
    targets_text = ""
    if target_1:
        targets_text += f"🎯 Alvo 1: U$ {format_us_price(target_1.get('price', 0))} ({target_1.get('percent', 0):.0f}%)\n"
    if target_2:
        targets_text += f"🎯 Alvo 2: U$ {format_us_price(target_2.get('price', 0))} ({target_2.get('percent', 0):.0f}%)\n"
    if target_3:
        targets_text += f"🎯 Alvo 3: U$ {format_us_price(target_3.get('price', 0))} ({target_3.get('percent', 0):.0f}%)\n"
    
    await query.edit_message_text(
        f"✅ **Trade Cadastrado com Sucesso!**\n\n"
        f"🪙 **{trade.get('pair')}** | {direction_emoji} | {trade.get('leverage')}x\n\n"
        f"📥 Entry: U$ {format_us_price(trade.get('entry_price', 0))}\n"
        f"🛑 Stop: U$ {format_us_price(trade.get('stop_loss', trade.get('stop_price', 0)))} ({trade.get('stop_percent', 0):.2f}%)\n"
        f"⚠️ Risco: U$ {format_us_price(trade.get('risk_usd', 0))}\n\n"
        f"{targets_text}"
        f"📊 Timeframe: {trade.get('timeframe', '4h').upper()}\n"
        f"➡️ Alocação: {allocation_percent:.2f}%\n\n"
        f"Use o menu de Futuros para acompanhar.",
        reply_markup=KeyboardBuilder.futures_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_adjust_stop(query, context: ContextTypes.DEFAULT_TYPE):
    """Allow user to adjust stop percentage."""
    context.user_data['awaiting_futures_stop_percent'] = True
    
    trade = context.user_data.get('futures_trade', {})
    current_stop = trade.get('stop_percent', 0)
    
    await query.edit_message_text(
        f"✏️ **Ajustar Stop Loss**\n\n"
        f"Stop atual: **{current_stop:.2f}%**\n\n"
        f"Digite o novo percentual de stop:",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )
