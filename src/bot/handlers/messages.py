"""
Telegram bot message handlers for user input.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from datetime import datetime
import re

from src.database import get_async_session, UserRepository, AssetRepository, EntryRepository
from src.database.repositories import FuturesRepository, AdminRepository
from src.services.market_data_service import market_data_service
from src.services.tradingview_service import TradingViewService
from src.services.trend_analysis_service import trend_analysis_service
from src.utils import KeyboardBuilder, MessageFormatter
from src.utils.logger import get_logger
from src.config.settings import settings
from src.core import MAJOR_COINS

logger = get_logger(__name__)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages based on user state."""
    user = update.effective_user
    text = update.message.text.strip()
    state = context.user_data.get('state')
    registration_step = context.user_data.get('registration_step')
    
    logger.debug(f"Message received: '{text}' from user {user.id}, state: {state}, reg_step: {registration_step}")
    
    # Handle registration flow first
    if registration_step:
        await handle_registration_input(update, context, text)
        return
    
    # Check if user is registered before processing other messages
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        db_user = await user_repo.get_by_telegram_id(user.id)
        
        if not db_user or not db_user.is_registered or not db_user.accepted_terms:
            await update.message.reply_text(
                "❌ Você precisa completar seu cadastro primeiro.\n\n"
                "Use /start para iniciar.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        if db_user.is_banned:
            await update.message.reply_text(
                "🚫 Sua conta foi suspensa.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
    
    # Check for futures-related awaiting states
    if context.user_data.get('awaiting_futures_pair'):
        await handle_futures_pair_input(update, context, text)
        return
    elif context.user_data.get('awaiting_futures_entry'):
        await handle_futures_entry_input(update, context, text)
        return
    elif context.user_data.get('awaiting_futures_stop_loss'):
        await handle_futures_stop_loss_input(update, context, text)
        return
    elif context.user_data.get('awaiting_futures_targets'):
        await handle_futures_targets_input(update, context, text)
        return
    elif context.user_data.get('awaiting_futures_custom_leverage'):
        await handle_futures_custom_leverage_input(update, context, text)
        return
    elif context.user_data.get('awaiting_futures_stop_percent'):
        await handle_futures_stop_percent_input(update, context, text)
        return
    elif context.user_data.get('awaiting_futures_timeframe'):
        await handle_futures_timeframe_input(update, context, text)
        return
    elif context.user_data.get('awaiting_futures_quantity'):
        await handle_futures_quantity_input(update, context, text)
        return
    elif context.user_data.get('awaiting_futures_margin'):
        await handle_futures_margin_input(update, context, text)
        return
    elif context.user_data.get('awaiting_futures_close_price'):
        await handle_futures_close_price_input(update, context, text)
        return
    elif context.user_data.get('awaiting_futures_sltp'):
        await handle_futures_sltp_input(update, context, text)
        return
    elif context.user_data.get('awaiting_futures_balance'):
        await handle_futures_balance_input(update, context, text)
        return
    elif context.user_data.get('awaiting_futures_risk_percent'):
        await handle_futures_risk_percent_input(update, context, text)
        return
    elif context.user_data.get('awaiting_admin_ban_id'):
        await handle_admin_ban_input(update, context, text)
        return
    
    # Check for trend analysis awaiting state
    if context.user_data.get('awaiting') == 'trend_symbol':
        await handle_trend_symbol_input(update, context, text)
        return
    
    # Regular states
    if state == 'waiting_coin_search':
        await handle_coin_search_input(update, context, text)
    elif state == 'searching_coin':
        await handle_coin_search_input(update, context, text, info_only=True)
    elif state == 'waiting_quantity':
        await handle_quantity_input(update, context, text)
    elif state == 'waiting_price':
        await handle_price_input(update, context, text)
    elif state == 'waiting_total_invested':
        await handle_total_invested_input(update, context, text)
    elif state == 'waiting_entry_quantity':
        await handle_entry_quantity_input(update, context, text)
    elif state == 'waiting_entry_price':
        await handle_entry_price_input(update, context, text)
    elif state == 'waiting_sell_quantity':
        await handle_sell_quantity_input(update, context, text)
    elif state == 'waiting_sell_price':
        await handle_sell_price_input(update, context, text)
    elif state == 'waiting_reserve_target':
        await handle_reserve_target_input(update, context, text)
    else:
        # No active state, show menu
        await update.message.reply_text(
            "📱 Use o menu para navegar:",
            reply_markup=KeyboardBuilder.main_menu()
        )


async def handle_registration_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle registration flow inputs."""
    step = context.user_data.get('registration_step')
    user = update.effective_user
    
    if step == 'name':
        # Validate name (minimum 3 characters)
        if len(text) < 3:
            await update.message.reply_text(
                "❌ Nome muito curto. Digite seu nome completo:",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        context.user_data['reg_name'] = text
        context.user_data['registration_step'] = 'phone'
        
        await update.message.reply_text(
            f"✅ Nome: **{text}**\n\n"
            "📝 **Etapa 2/4 - Telefone**\n\n"
            "Digite seu **número de telefone** (com DDD):\n"
            "Exemplo: `11999998888`",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif step == 'phone':
        # Clean phone number
        phone = re.sub(r'[^0-9]', '', text)
        
        if len(phone) < 10:
            await update.message.reply_text(
                "❌ Número inválido. Digite um telefone válido com DDD:\n"
                "Exemplo: `11999998888`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        context.user_data['reg_phone'] = phone
        context.user_data['registration_step'] = 'birth_date'
        
        await update.message.reply_text(
            f"✅ Telefone: **{phone}**\n\n"
            "📝 **Etapa 3/4 - Data de Nascimento**\n\n"
            "Digite sua **data de nascimento**:\n"
            "Formato: `DD/MM/AAAA`\n"
            "Exemplo: `15/03/1990`",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif step == 'birth_date':
        # Validate date format
        date_pattern = re.compile(r'^(\d{2})/(\d{2})/(\d{4})$')
        match = date_pattern.match(text)
        
        if not match:
            await update.message.reply_text(
                "❌ Formato inválido. Use: `DD/MM/AAAA`\n"
                "Exemplo: `15/03/1990`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        day, month, year = match.groups()
        try:
            # Basic validation
            birth = datetime(int(year), int(month), int(day))
            if birth > datetime.now():
                raise ValueError("Future date")
            if int(year) < 1900:
                raise ValueError("Too old")
        except:
            await update.message.reply_text(
                "❌ Data inválida. Verifique e tente novamente:",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        context.user_data['reg_birth_date'] = text
        context.user_data['registration_step'] = 'futures_balance'
        
        await update.message.reply_text(
            f"✅ Data de nascimento: **{text}**\n\n"
            "📝 **Etapa 4/4 - Capital para Futuros**\n\n"
            "💰 Informe em **USDT** o valor disponível para investir em **Futuros**:\n\n"
            "Este valor será usado para:\n"
            "• Calcular sugestões de exposição\n"
            "• Sugerir stop loss adequados\n"
            "• Informar riscos das operações\n\n"
            "Digite o valor (ou `0` se não pretende operar futuros):",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif step == 'futures_balance':
        try:
            balance = float(text.replace(',', '.').replace('$', '').strip())
            if balance < 0:
                raise ValueError()
        except:
            await update.message.reply_text(
                "❌ Valor inválido. Digite apenas números:\n"
                "Exemplo: `1000` ou `500.50`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        context.user_data['reg_futures_balance'] = balance
        
        # Complete registration
        async with get_async_session() as session:
            user_repo = UserRepository(session)
            
            db_user = await user_repo.complete_registration(
                telegram_id=user.id,
                full_name=context.user_data['reg_name'],
                phone=context.user_data['reg_phone'],
                birth_date=context.user_data['reg_birth_date'],
                futures_balance=balance
            )
            await session.commit()
        
        # Clear registration data but keep step for terms
        reg_name = context.user_data['reg_name']
        context.user_data.clear()
        context.user_data['registration_step'] = 'terms'
        
        # Show terms
        from src.bot.handlers.commands import show_terms
        await show_terms(update, context, reg_name)


async def handle_futures_balance_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle futures balance update input."""
    user = update.effective_user
    
    try:
        balance = float(text.replace(',', '.').replace('$', '').strip())
        if balance < 0:
            raise ValueError()
    except:
        await update.message.reply_text(
            "❌ Valor inválido. Digite apenas números:\n"
            "Exemplo: `1000` ou `500.50`",
            reply_markup=KeyboardBuilder.back_to_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        await user_repo.update_futures_balance(user.id, balance)
        await session.commit()
    
    context.user_data.pop('awaiting_futures_balance', None)
    
    await update.message.reply_text(
        f"✅ **Saldo de Futuros atualizado!**\n\n"
        f"💰 Novo saldo: **${balance:,.2f} USDT**",
        reply_markup=KeyboardBuilder.back_to_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_risk_percent_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle futures risk percent configuration input."""
    user = update.effective_user
    
    try:
        risk_pct = float(text.replace(',', '.').replace('%', ''))
        if risk_pct < 0.5 or risk_pct > 20:
            raise ValueError()
    except:
        await update.message.reply_text(
            "❌ Valor inválido. Digite um percentual entre 0.5 e 20:\n"
            "Exemplo: `5` para 5%",
            reply_markup=KeyboardBuilder.back_to_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        await user_repo.update_futures_risk_percent(user.id, risk_pct)
        await session.commit()
    
    context.user_data.pop('awaiting_futures_risk_percent', None)
    
    await update.message.reply_text(
        f"✅ **Gerenciamento de risco atualizado para {risk_pct}% por trade**\n"
        f"_(definido pelo usuário)_\n\n"
        f"💡 Nossa sugestão continua sendo **5%** do valor total da carteira de futuros.\n\n"
        f"Com essa configuração:\n"
        f"• Risco máximo por operação = {risk_pct}% da sua carteira\n"
        f"• Recomendamos diversificar em múltiplas operações menores",
        reply_markup=KeyboardBuilder.back_to_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_admin_ban_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle admin ban user input."""
    user = update.effective_user
    action = context.user_data.get('admin_action', 'ban')
    
    try:
        target_id = int(text.strip())
    except:
        await update.message.reply_text(
            "❌ ID inválido. Digite o ID numérico do usuário:",
            reply_markup=KeyboardBuilder.back_to_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    async with get_async_session() as session:
        admin_repo = AdminRepository(session)
        user_repo = UserRepository(session)
        
        # Get admin user
        admin_user = await user_repo.get_by_telegram_id(user.id)
        
        if action == 'ban':
            success = await admin_repo.ban_user(admin_user.id, target_id)
            action_text = "banido"
        else:
            success = await admin_repo.unban_user(admin_user.id, target_id)
            action_text = "desbanido"
        
        await session.commit()
    
    context.user_data.pop('awaiting_admin_ban_id', None)
    context.user_data.pop('admin_action', None)
    
    if success:
        await update.message.reply_text(
            f"✅ Usuário {target_id} foi **{action_text}** com sucesso!",
            reply_markup=KeyboardBuilder.admin_panel(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            f"❌ Usuário não encontrado ou operação não permitida.",
            reply_markup=KeyboardBuilder.admin_panel(),
            parse_mode=ParseMode.MARKDOWN
        )


async def handle_coin_search_input(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                    query: str, info_only: bool = False):
    """Handle coin search input using OKX."""
    # Check if user has preset coin (USDT addition)
    preset_coin = context.user_data.get('preset_coin')
    
    if preset_coin:
        # Skip search, go directly to quantity
        context.user_data['selected_coin_symbol'] = preset_coin
        context.user_data['selected_coin_name'] = preset_coin
        context.user_data['state'] = 'waiting_quantity'
        
        try:
            quantity = float(query.replace(',', '.'))
            if quantity <= 0:
                raise ValueError()
                
            context.user_data['quantity'] = quantity
            context.user_data['state'] = 'waiting_price'
            
            await update.message.reply_text(
                f"📦 **Quantidade:** {quantity}\n\n"
                f"Digite o **preço de compra** (normalmente $1.00 para USDT):",
                reply_markup=KeyboardBuilder.cancel_action(),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        except:
            await update.message.reply_text(
                "❌ Por favor, insira um número válido.",
                reply_markup=KeyboardBuilder.cancel_action()
            )
            return
    
    await update.message.reply_text("🔍 Buscando no TradingView...")
    
    tv = TradingViewService()
    try:
        coins = await tv.search_coins(query)
    finally:
        await tv.close()
    
    if not coins:
        await update.message.reply_text(
            f"❌ Nenhuma moeda encontrada para '{query}'.\n\n"
            "Tente outro nome ou símbolo (ex: BTC, ETH, SOL).",
            reply_markup=KeyboardBuilder.cancel_action()
        )
        return
    
    if info_only:
        context.user_data['state'] = 'searching_coin'
    
    # Build keyboard with results
    keyboard = []
    for coin in coins[:8]:
        symbol = coin.get('symbol', '???')
        name = coin.get('name', symbol)
        price = coin.get('price', 0)
        
        keyboard.append([
            InlineKeyboardButton(
                f"{symbol.upper()} - {name[:25]} (${price:,.4f})",
                callback_data=f"select_coin_{symbol}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Cancelar", callback_data="cancel")])
    
    await update.message.reply_text(
        f"📋 **Resultados para '{query}':**\n\n"
        "Selecione uma moeda:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_quantity_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle quantity input when adding an asset."""
    try:
        quantity = float(text.replace(',', '.'))
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor, insira um número válido para a quantidade.\n\n"
            "Exemplo: `0.5`, `100`, `1.5`",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    context.user_data['quantity'] = quantity
    context.user_data['state'] = 'waiting_price'
    
    coin_symbol = context.user_data.get('selected_coin_symbol', '???')
    current_price = context.user_data.get('selected_coin_price', 0)
    
    await update.message.reply_text(
        f"💰 **Adicionar {coin_symbol.upper()}**\n\n"
        f"📊 **Preço Atual:** ${current_price:,.6f}\n"
        f"📦 **Quantidade:** {quantity:,.6f}\n\n"
        f"\u2796\u2796\u2796\u2796\u2796\u2796\u2796\u2796\u2796\u2796\n\n"
        f"💵 **Passo 2/3:** Digite o **preço de compra** (em USD):\n\n"
        f"💡 _Dica: Preço atual \u00e9 ${current_price:,.6f}_",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle price input when adding an asset."""
    from src.utils.formatters import parse_us_number, format_us_price
    
    try:
        price = parse_us_number(text)
        if price <= 0:
            raise ValueError("Price must be positive")
    except (ValueError, Exception):
        await update.message.reply_text(
            "❌ Por favor, insira um número válido para o preço.\n\n"
            "**Formatos aceitos:**\n"
            "• `99000` → 99,000.00\n"
            "• `99,000` → 99,000.00\n"
            "• `99,000.00` → 99,000.00\n"
            "• `0.00000001` → 0.00000001\n"
            "• `$999,999.00` → 999,999.00\n"
            "• `0.00015` → 0.00015",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    symbol = context.user_data.get('selected_coin_symbol')
    current_price = context.user_data.get('selected_coin_price', 0)
    
    context.user_data['purchase_price'] = price
    context.user_data['state'] = 'waiting_total_invested'
    
    await update.message.reply_text(
        f"💰 **Adicionar {symbol.upper()}**\n\n"
        f"📊 **Preço Atual:** U$ {format_us_price(current_price)}\n"
        f"💵 **Preço de Compra:** U$ {format_us_price(price)}\n\n"
        f"\u2796\u2796\u2796\u2796\u2796\u2796\u2796\u2796\u2796\u2796\n\n"
        f"💸 **Passo 2/2:** Digite o **valor total investido** (em USD):",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_total_invested_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle total invested input when adding an asset."""
    from src.utils.formatters import parse_us_number, format_us_price
    
    try:
        total_invested = parse_us_number(text)
        if total_invested <= 0:
            raise ValueError("Total must be positive")
    except (ValueError, Exception):
        await update.message.reply_text(
            "❌ Por favor, insira um número válido para o total investido.\n\n"
            "**Formatos aceitos:**\n"
            "• `100` → 100.00\n"
            "• `1,500.50` → 1,500.50\n"
            "• `$25,000` → 25,000.00",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    symbol = context.user_data.get('selected_coin_symbol')
    name = context.user_data.get('selected_coin_name', symbol)
    price = context.user_data.get('purchase_price')
    current_price = context.user_data.get('selected_coin_price', 0)
    
    # Calculate quantity automatically: quantity = total_invested / purchase_price
    quantity = total_invested / price if price > 0 else 0
    
    context.user_data['total_invested'] = total_invested
    context.user_data['quantity'] = quantity
    context.user_data['state'] = None
    
    # Check if this is a stablecoin (USDT reserve)
    stablecoins = ["USDT", "USDC", "BUSD", "DAI", "TUSD"]
    is_stablecoin = symbol.upper() in stablecoins
    
    if is_stablecoin:
        # Special display for stablecoins (reserve) - simplified view
        message = (
            f"💵 **Reserva de Caixa**\n\n"
            f"🪙 **{symbol.upper()}** ({name})\n\n"
            f"💸 **Total Investido:** U$ {format_us_price(total_invested)}\n"
            f"📦 **Quantidade:** {quantity:,.2f} {symbol.upper()}\n\n"
            f"\u2796\u2796\u2796\u2796\u2796\u2796\u2796\u2796\u2796\u2796\n\n"
            f"💡 **Reserva de caixa para novos investimentos**\n\n"
            f"Esta reserva será utilizada para:\n"
            f"• Comprar novos ativos\n"
            f"• Fazer preço médio em quedas\n"
            f"• Aproveitar oportunidades de mercado\n\n"
            f"Confirma ou deseja corrigir algum dado?"
        )
    else:
        # Standard display for regular assets
        current_value = quantity * current_price
        profit_loss = current_value - total_invested
        profit_percent = (profit_loss / total_invested * 100) if total_invested > 0 else 0
        pl_emoji = "🟢" if profit_loss >= 0 else "🔴"
        
        message = (
            f"📋 **Resumo do Ativo**\n\n"
            f"🪙 **{symbol.upper()}** ({name})\n\n"
            f"💵 **Preço de Compra:** U$ {format_us_price(price)}\n"
            f"💸 **Total Investido:** U$ {format_us_price(total_invested)}\n"
            f"📦 **Quantidade:** {quantity:,.6f} _(calculado)_\n\n"
            f"\u2796\u2796\u2796\u2796\u2796\u2796\u2796\u2796\u2796\u2796\n\n"
            f"📊 **Preço Atual:** U$ {format_us_price(current_price)}\n"
            f"📈 **Valorização do investimento inicial:** U$ {format_us_price(current_value)}\n"
            f"{pl_emoji} **Lucro/Prejuízo:** U$ {format_us_price(profit_loss)} ({profit_percent:+.2f}%)\n\n"
            f"Confirma ou deseja corrigir algum dado?"
        )
    
    await update.message.reply_text(
        message,
        reply_markup=KeyboardBuilder.confirm_or_correct_asset(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_entry_quantity_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle invested value input for new entry (Step 2)."""
    from src.utils.formatters import parse_us_number, format_us_price
    
    try:
        total_invested = parse_us_number(text)
        if total_invested <= 0:
            raise ValueError("Value must be positive")
    except (ValueError, Exception):
        await update.message.reply_text(
            "❌ Por favor, insira um valor válido.\n\n"
            "**Formatos aceitos:**\n"
            "• `100` → 100.00\n"
            "• `1,500.50` → 1,500.50\n"
            "• `$25,000` → 25,000.00",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Get entry price from previous step
    entry_price = context.user_data.get('entry_price', 0)
    
    # Calculate quantity from invested value and price
    quantity = total_invested / entry_price if entry_price > 0 else 0
    
    context.user_data['entry_quantity'] = quantity
    context.user_data['entry_total_invested'] = total_invested
    
    user = update.effective_user
    asset_id = context.user_data.get('entry_asset_id')
    
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        asset_repo = AssetRepository(session)
        entry_repo = EntryRepository(session)
        
        db_user = await user_repo.get_by_telegram_id(user.id)
        if not db_user:
            await update.message.reply_text(
                "❌ Usuário não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        asset = await asset_repo.get_by_id(asset_id)
        if not asset or asset.user_id != db_user.id:
            await update.message.reply_text(
                "❌ Ativo não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        # Create new entry with current date
        entry_date = datetime.now()
        await entry_repo.create_entry(
            asset_id=asset_id,
            entry_price=entry_price,
            quantity=quantity,
            total_value=total_invested,
            notes=f"Entrada em {entry_date.strftime('%d/%m/%Y')}",
            entry_date=entry_date
        )
        
        # Update asset total quantity
        new_quantity = asset.quantity + quantity
        await asset_repo.update_asset(asset_id, quantity=new_quantity)
        
        # Get updated asset and all entries
        asset = await asset_repo.get_by_id(asset_id)
        entries = await entry_repo.get_asset_entries(asset_id)
    
    context.user_data.clear()
    
    # Build entries history
    entries_text = ""
    for i, entry in enumerate(entries, 1):  # Show all entries
        entry_date_str = entry.entry_date.strftime('%d/%m/%Y') if entry.entry_date else 'N/A'
        entries_text += (
            f"📦 **Quantidade:** {entry.quantity:,.6f}\n"
            f"💰 **Preço:** U$ {format_us_price(entry.entry_price)}\n"
            f"🗓 **Data de compra:** {entry_date_str}\n\n"
        )
    
    await update.message.reply_text(
        f"✅ **Nova Entrada Adicionada!**\n\n"
        f"🪙 **{asset.symbol.upper()}**\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📜 **Histórico de Entradas:**\n\n"
        f"{entries_text}"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💵 **Valor total investido nesse ativo:** U$ {format_us_price(asset.total_invested)}\n\n"
        f"📊 **Quantidade total de ativos:** {asset.quantity:,.6f}\n"
        f"📈 **Preço médio:** U$ {format_us_price(asset.average_price)}",
        reply_markup=KeyboardBuilder.asset_actions(asset_id),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_entry_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle price input for new entry (Step 1)."""
    from src.utils.formatters import parse_us_number, format_us_price
    
    try:
        price = parse_us_number(text)
        if price <= 0:
            raise ValueError("Price must be positive")
    except (ValueError, Exception):
        await update.message.reply_text(
            "❌ Por favor, insira um número válido para o preço.\n\n"
            "**Formatos aceitos:**\n"
            "• `99000` → 99,000.00\n"
            "• `99,000.00` → 99,000.00\n"
            "• `0.00000001` → 0.00000001",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Store price and move to step 2
    context.user_data['entry_price'] = price
    context.user_data['state'] = 'waiting_entry_quantity'
    
    await update.message.reply_text(
        f"✅ **Valor de compra registrado:** U$ {format_us_price(price)}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"**2️⃣ Quantidade investida na nova compra U$:**\n\n"
        f"Digite o valor total que você investiu nesta compra.\n\n"
        f"_Exemplo: 100, 1500.50, $25,000_",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_sell_quantity_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle quantity input for selling."""
    try:
        quantity = float(text.replace(',', '.'))
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor, insira um número válido para a quantidade.",
            reply_markup=KeyboardBuilder.cancel_action()
        )
        return
    
    context.user_data['sell_quantity'] = quantity
    context.user_data['state'] = 'waiting_sell_price'
    
    await update.message.reply_text(
        f"📤 **Quantidade a vender:** {quantity}\n\n"
        "Agora digite o **preço de venda** (em USD):",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_sell_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle price input for selling."""
    from src.utils.formatters import parse_us_number, format_us_price
    
    try:
        price = parse_us_number(text)
        if price <= 0:
            raise ValueError("Price must be positive")
    except (ValueError, Exception):
        await update.message.reply_text(
            "❌ Por favor, insira um número válido para o preço.\n\n"
            "**Formatos aceitos:**\n"
            "• `99000` → 99,000.00\n"
            "• `99,000.00` → 99,000.00\n"
            "• `0.00000001` → 0.00000001",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    user = update.effective_user
    asset_id = context.user_data.get('sell_asset_id')
    quantity = context.user_data.get('sell_quantity')
    
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        asset_repo = AssetRepository(session)
        
        db_user = await user_repo.get_by_telegram_id(user.id)
        if not db_user:
            await update.message.reply_text(
                "❌ Usuário não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        asset = await asset_repo.get_by_id(asset_id)
        if not asset or asset.user_id != db_user.id:
            await update.message.reply_text(
                "❌ Ativo não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        if quantity > asset.quantity:
            await update.message.reply_text(
                f"❌ Quantidade inválida.\n"
                f"Você possui apenas {asset.quantity:,.6f} {asset.symbol.upper()}.",
                reply_markup=KeyboardBuilder.cancel_action()
            )
            return
        
        # Calculate profit
        sell_value = quantity * price
        cost_basis = quantity * (asset.average_price or asset.purchase_price)
        profit = sell_value - cost_basis
        profit_pct = (profit / cost_basis) * 100 if cost_basis > 0 else 0
        
        # Update asset quantity
        new_quantity = asset.quantity - quantity
        
        if new_quantity <= 0:
            # Remove asset completely
            await asset_repo.delete_asset(asset_id)
            symbol = asset.symbol.upper()
            context.user_data.clear()
            
            emoji = "🟢" if profit >= 0 else "🔴"
            
            await update.message.reply_text(
                f"✅ **Venda Total Registrada!**\n\n"
                f"🪙 **{symbol}**\n\n"
                f"📤 **Vendido:** {quantity:,.6f}\n"
                f"💵 **Preço de Venda:** ${price:,.6f}\n"
                f"💰 **Valor Total:** ${sell_value:,.2f}\n"
                f"{emoji} **P/L:** ${profit:+,.2f} ({profit_pct:+.2f}%)\n\n"
                f"O ativo foi removido da sua carteira.",
                reply_markup=KeyboardBuilder.back_to_menu(),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        await asset_repo.update_asset(asset_id, quantity=new_quantity)
        
        # Get updated asset
        asset = await asset_repo.get_by_id(asset_id)
    
    context.user_data.clear()
    
    emoji = "🟢" if profit >= 0 else "🔴"
    
    await update.message.reply_text(
        f"✅ **Venda Registrada!**\n\n"
        f"🪙 **{asset.symbol.upper()}**\n\n"
        f"📤 **Vendido:** {quantity:,.6f}\n"
        f"💵 **Preço de Venda:** ${price:,.6f}\n"
        f"💰 **Valor Total:** ${sell_value:,.2f}\n"
        f"{emoji} **P/L:** ${profit:+,.2f} ({profit_pct:+.2f}%)\n\n"
        f"📦 **Quantidade Restante:** {asset.quantity:,.6f}",
        reply_markup=KeyboardBuilder.asset_actions(asset_id),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_reserve_target_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle reserve target percentage input."""
    try:
        target = float(text.replace(',', '.').replace('%', ''))
        if target < 0 or target > 100:
            raise ValueError("Target must be between 0 and 100")
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor, insira um número válido entre 0 e 100.\n\n"
            "Exemplo: `15` para 15%",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    user = update.effective_user
    
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        db_user = await user_repo.get_by_telegram_id(user.id)
        
        if db_user:
            await user_repo.update_user(db_user.id, reserve_target_percent=target)
    
    context.user_data.clear()
    
    await update.message.reply_text(
        f"✅ **Meta de Reserva Atualizada!**\n\n"
        f"💵 Nova meta: {target}%\n\n"
        f"Você receberá alertas quando sua reserva em USDT estiver abaixo desta meta.",
        reply_markup=KeyboardBuilder.back_to_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


# ==================== FUTURES MESSAGE HANDLERS ====================

async def handle_futures_pair_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """
    Handle futures pair symbol input - Step 1 of new trade flow.
    Accepts formats: BTC/USDT, BTCUSDT, BTC, BTC.P, USDT.P, TOTAL, etc.
    """
    from src.utils.formatters import format_us_price, parse_us_number, MessageFormatter
    from src.services.risk_management import risk_service
    
    pair_input = text.strip()
    user = update.effective_user
    
    # Allow flexible pair formats: BTC/USDT, BTCUSDT, BTC, BTC.P, TOTAL, etc.
    # Normalize: keep original format for display, clean for processing
    display_pair = pair_input.upper()
    
    # Clean pair for price lookup
    clean_pair = pair_input.upper().replace("/", "").replace("-", "").replace(".P", "").replace(".p", "")
    
    # Check if user provided full pair or just base symbol
    quote_currencies = ["USDT", "USDC", "USD", "BTC", "ETH", "BNB", "BUSD"]
    
    has_quote = any(clean_pair.endswith(q) for q in quote_currencies)
    
    if has_quote:
        pair = clean_pair
        for q in quote_currencies:
            if clean_pair.endswith(q):
                symbol = clean_pair[:-len(q)]
                break
    else:
        symbol = clean_pair
        pair = f"{symbol}USDT"
    
    # Check if it's a valid symbol using TradingView
    await update.message.reply_text("🔍 Verificando par e obtendo preço atual...")
    
    tv = TradingViewService()
    current_price = 0
    try:
        price_data = await tv.get_price(symbol)
        if price_data:
            current_price = price_data.get('price', 0)
    except Exception as e:
        logger.warning(f"Could not get price for {symbol}: {e}")
    finally:
        await tv.close()
    
    # Allow to continue even without price (user will enter manually)
    is_altcoin = symbol not in MAJOR_COINS
    
    # Get user's futures balance and risk config
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        futures_repo = FuturesRepository(session)
        
        db_user = await user_repo.get_by_telegram_id(user.id)
        futures_balance = db_user.futures_balance or 0
        risk_percent = db_user.futures_risk_percent or 5.0
        
        # Get total open risk
        open_risk = await futures_repo.get_total_open_risk(db_user.id)
    
    # Calculate available risk
    max_risk = futures_balance * (risk_percent / 100)
    available_risk = max_risk - open_risk
    
    # Store trade data with step tracking
    context.user_data['futures_trade'] = {
        'step': 1,
        'pair': display_pair if "/" in pair_input else pair,
        'symbol': symbol,
        'is_altcoin': is_altcoin,
        'current_price': current_price,
        'futures_balance': futures_balance,
        'risk_percent': risk_percent,
        'open_risk': open_risk,
        'max_risk': max_risk,
        'available_risk': available_risk,
        'user_id': db_user.id,
        'targets': []
    }
    context.user_data.pop('awaiting_futures_pair', None)
    
    # Build step summary
    step_summary = MessageFormatter.futures_registration_step(1, context.user_data['futures_trade'])
    
    altcoin_warning = ""
    if is_altcoin:
        altcoin_warning = "\n⚠️ **ATENÇÃO:** Este é um altcoin. Alavancagem >3x é arriscada!\n"
    
    price_hint = ""
    if current_price > 0:
        price_hint = f"💡 Preço atual: U$ {format_us_price(current_price)}\n\n"
    else:
        price_hint = "⚠️ Não foi possível obter preço atual. Digite manualmente.\n\n"
    
    await update.message.reply_text(
        step_summary + "\n\n"
        f"{altcoin_warning}"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ **Etapa 1/9 concluída!**\n\n"
        "📝 **Etapa 2/9 - Preço de Compra**\n\n"
        f"Digite o **preço de compra** da operação:\n\n"
        f"{price_hint}"
        "_Formato: 95,699.90 (padrão US)_",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )
    
    context.user_data['awaiting_futures_entry'] = True


async def handle_futures_entry_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle futures entry price input - Step 2 of new trade flow."""
    from src.utils.formatters import format_us_price, parse_us_number, MessageFormatter
    
    try:
        price = parse_us_number(text)
        if price <= 0:
            raise ValueError()
    except:
        await update.message.reply_text(
            "❌ Valor inválido.\n\n"
            "Use o formato: `95,699.90` (vírgula para milhares, ponto para decimais)\n"
            "Exemplos: `95,699.90` | `1,234.56` | `0.5432`",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    context.user_data['futures_trade']['entry_price'] = price
    context.user_data['futures_trade']['step'] = 2
    context.user_data.pop('awaiting_futures_entry', None)
    
    trade = context.user_data['futures_trade']
    step_summary = MessageFormatter.futures_registration_step(2, trade)
    
    await update.message.reply_text(
        step_summary + "\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ **Etapa 2/9 concluída!**\n\n"
        "📝 **Etapa 3/9 - Valor Investido**\n\n"
        "Digite o **valor investido** (margem/colateral em USD):\n\n"
        f"💰 Sua carteira de futuros: U$ {format_us_price(trade.get('futures_balance', 0))}\n\n"
        "Exemplos: `100`, `500.50`, `1,000.00`",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )
    
    context.user_data['awaiting_futures_margin'] = True


async def handle_futures_custom_leverage_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle custom leverage input."""
    from src.utils.formatters import format_us_price, MessageFormatter
    
    try:
        leverage = int(text.replace('x', '').replace('X', '').strip())
        if leverage < 1 or leverage > 125:
            raise ValueError()
    except:
        await update.message.reply_text(
            "❌ Valor inválido.\n\n"
            "Digite um número entre 1 e 125.\n"
            "Exemplos: `5`, `10x`, `25`",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    context.user_data['futures_trade']['leverage'] = leverage
    context.user_data['futures_trade']['step'] = 5
    context.user_data.pop('awaiting_futures_custom_leverage', None)
    
    trade = context.user_data['futures_trade']
    is_altcoin = trade.get('is_altcoin', False)
    entry_price = trade.get('entry_price', 0)
    side = trade.get('side', 'long')
    margin = trade.get('margin', 0)
    
    # Calculate quantity and position value
    position_value = margin * leverage
    quantity = position_value / entry_price if entry_price > 0 else 0
    
    context.user_data['futures_trade']['quantity'] = quantity
    context.user_data['futures_trade']['position_value'] = position_value
    
    # Calculate liquidation price
    liquidation_percent = 100 / leverage
    if side == 'long':
        liquidation_price = entry_price * (1 - liquidation_percent / 100)
    else:
        liquidation_price = entry_price * (1 + liquidation_percent / 100)
    
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
    
    step_summary = MessageFormatter.futures_registration_step(5, trade)
    
    await update.message.reply_text(
        step_summary + "\n\n"
        f"💵 **Valor Investido:** U$ {format_us_price(margin)}\n"
        f"📊 **Posição Total:** U$ {format_us_price(position_value)} ({leverage}x)\n"
        f"📦 **Quantidade:** {quantity:,.6f} contratos\n"
        f"{risk_warning}"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ **Etapa 5/9 concluída!**\n\n"
        "📝 **Etapa 6/9 - Stop Loss**\n\n"
        "Digite o **preço do Stop Loss**:\n\n"
        f"💡 Preço de compra: U$ {format_us_price(entry_price)}\n"
        f"💥 Preço de liquidação: U$ {format_us_price(liquidation_price)}\n\n"
        "_Recomendação: Stop antes da liquidação!_",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )
    
    context.user_data['awaiting_futures_stop_loss'] = True


async def handle_futures_stop_loss_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle stop loss price input - Step 6 of new trade flow."""
    from src.utils.formatters import format_us_price, parse_us_number, MessageFormatter
    
    try:
        stop_loss = parse_us_number(text)
        if stop_loss <= 0:
            raise ValueError()
    except:
        await update.message.reply_text(
            "❌ Valor inválido.\n\n"
            "Digite o preço do stop loss.\n"
            "Exemplo: `88,000.00`",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    trade = context.user_data['futures_trade']
    entry_price = trade.get('entry_price', 0)
    side = trade.get('side', 'long')
    leverage = trade.get('leverage', 1)
    futures_balance = trade.get('futures_balance', 0)
    margin = trade.get('margin', 0)
    open_risk = trade.get('open_risk', 0)  # Risco já em uso
    max_risk = trade.get('max_risk', futures_balance * 0.05)  # Risco máximo permitido
    available_risk = max_risk - open_risk  # Risco disponível
    
    # Validar direção do stop
    if side == 'long' and stop_loss >= entry_price:
        await update.message.reply_text(
            "❌ Para **LONG**, o stop loss deve ser **menor** que o preço de entrada.\n\n"
            f"📥 Preço de entrada: U$ {format_us_price(entry_price)}\n"
            f"🛑 Stop informado: U$ {format_us_price(stop_loss)}\n\n"
            "Digite um valor menor:",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    elif side == 'short' and stop_loss <= entry_price:
        await update.message.reply_text(
            "❌ Para **SHORT**, o stop loss deve ser **maior** que o preço de entrada.\n\n"
            f"📥 Preço de entrada: U$ {format_us_price(entry_price)}\n"
            f"🛑 Stop informado: U$ {format_us_price(stop_loss)}\n\n"
            "Digite um valor maior:",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Calculate stop % based on entry and stop loss
    if side == 'long':
        stop_percent = ((entry_price - stop_loss) / entry_price) * 100
    else:
        stop_percent = ((stop_loss - entry_price) / entry_price) * 100
    
    # Calculate risk in USD: Risco = (stop% / 100) * margem * alavancagem
    risk_usd = (stop_percent / 100) * margin * leverage
    
    # Verificar se o risco excede o disponível
    if risk_usd > available_risk and available_risk > 0:
        await update.message.reply_text(
            f"⚠️ **ALERTA DE GERENCIAMENTO DE RISCO**\n\n"
            f"O risco deste trade (U$ {format_us_price(risk_usd)}) excede o risco disponível!\n\n"
            f"📊 **Seu gerenciamento de risco:**\n"
            f"   💰 Carteira: U$ {format_us_price(futures_balance)}\n"
            f"   ⚙️ Risco máximo ({trade.get('risk_percent', 5)}%): U$ {format_us_price(max_risk)}\n"
            f"   🔒 Risco em uso: U$ {format_us_price(open_risk)}\n"
            f"   ✅ Risco disponível: U$ {format_us_price(available_risk)}\n\n"
            f"🛑 **Este trade:**\n"
            f"   Distância do stop: {stop_percent:.2f}%\n"
            f"   Risco calculado: U$ {format_us_price(risk_usd)}\n\n"
            f"💡 **Opções:**\n"
            f"1. Aproxime o stop loss do preço de entrada\n"
            f"2. Reduza a margem investida\n"
            f"3. Feche outras posições para liberar risco\n\n"
            f"Digite um novo preço de stop:",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    context.user_data['futures_trade']['stop_loss'] = stop_loss
    context.user_data['futures_trade']['stop_percent'] = stop_percent
    context.user_data['futures_trade']['risk_usd'] = risk_usd
    context.user_data['futures_trade']['step'] = 6
    context.user_data.pop('awaiting_futures_stop_loss', None)
    
    step_summary = MessageFormatter.futures_registration_step(6, trade)
    
    # Calculate what % of max risk this trade uses
    risk_of_max = (risk_usd / max_risk * 100) if max_risk > 0 else 0
    risk_of_balance = (risk_usd / futures_balance * 100) if futures_balance > 0 else 0
    
    # Novo risco disponível após este trade
    new_available = available_risk - risk_usd
    
    await update.message.reply_text(
        step_summary + "\n\n"
        f"📊 **Análise do Stop Loss:**\n"
        f"• Distância do stop: {stop_percent:.2f}%\n"
        f"• Risco deste trade: U$ {format_us_price(risk_usd)}\n\n"
        f"💰 **Gerenciamento de Risco:**\n"
        f"• Risco máximo permitido: U$ {format_us_price(max_risk)}\n"
        f"• Risco já em uso: U$ {format_us_price(open_risk)}\n"
        f"• Este trade usa: U$ {format_us_price(risk_usd)} ({risk_of_max:.1f}% do máximo)\n"
        f"• Risco restante após: U$ {format_us_price(new_available)}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ **Etapa 6/9 concluída!**\n\n"
        "📝 **Etapa 7/9 - Alvos de Venda**\n\n"
        "Digite o **primeiro alvo de venda** no formato:\n"
        "`preço percentual`\n\n"
        "Exemplo: `99,000.00 50`\n"
        "_(significa vender 50% quando atingir U$ 99,000.00)_",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )
    
    context.user_data['awaiting_futures_targets'] = True
    context.user_data['futures_trade']['target_count'] = 1


async def handle_futures_targets_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle targets input - Step 6 of new trade flow."""
    from src.utils.formatters import format_us_price, parse_us_number, MessageFormatter
    
    # Limpar e separar os valores
    text = text.strip()
    
    # Tentar diferentes formatos de separação
    parts = None
    
    # Tentar separar por espaço
    if ' ' in text:
        parts = text.split()
    # Tentar separar por vírgula seguida de espaço ou apenas vírgula no final
    elif text.count(',') > 0:
        # Se tem mais de uma vírgula, pode ser formato "99,000,50" onde 50 é o percentual
        # Tentar encontrar o último número como percentual
        temp = text.replace(',', ' ').split()
        if len(temp) >= 2:
            parts = [' '.join(temp[:-1]).replace(' ', ','), temp[-1]]
    
    if not parts or len(parts) < 2:
        await update.message.reply_text(
            "❌ Formato inválido.\n\n"
            "Use: `preço percentual`\n"
            "Exemplos:\n"
            "• `99000 50` (vender 50% a U$ 99,000)\n"
            "• `0.00015 25` (vender 25% a U$ 0.00015)\n"
            "• `99,000.00 100` (vender 100% a U$ 99,000)",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        target_price = parse_us_number(parts[0])
        target_percent = float(parts[-1].replace('%', '').replace(',', '.'))
        
        # Apenas validar se são números positivos
        if target_price <= 0:
            raise ValueError("Preço deve ser maior que zero")
        if target_percent <= 0:
            raise ValueError("Percentual deve ser maior que zero")
        # Não limitar percentual máximo - permite 100% ou mais se necessário
            
    except Exception as e:
        await update.message.reply_text(
            f"❌ Valores inválidos.\n\n"
            "Use: `preço percentual`\n"
            "Exemplos:\n"
            "• `99000 50` (vender 50% a U$ 99,000)\n"
            "• `0.00015 25` (vender 25% a U$ 0.00015)\n"
            "• `99,000.00 100` (vender 100% a U$ 99,000)",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    trade = context.user_data['futures_trade']
    target_count = trade.get('target_count', 1)
    
    # Store target
    trade['targets'].append({
        'price': target_price,
        'percent': target_percent
    })
    
    # Also store in individual fields
    trade[f'target_{target_count}'] = {
        'price': target_price,
        'percent': target_percent
    }
    
    # Check total percent
    total_percent = sum(t.get('percent', 0) for t in trade['targets'])
    
    targets_summary = ""
    for i, t in enumerate(trade['targets'], 1):
        entry_price = trade.get('entry_price', 0)
        side = trade.get('side', 'long')
        profit_pct = ((t['price'] - entry_price) / entry_price * 100) if entry_price > 0 else 0
        if side == 'short':
            profit_pct = -profit_pct
        targets_summary += f"   🎯 Alvo {i}: U$ {format_us_price(t['price'])} > {t['percent']:.0f}% (Lucro {profit_pct:.1f}%)\n"
    
    if total_percent >= 100 or target_count >= 3:
        # Proceed to next step
        trade['step'] = 6
        context.user_data.pop('awaiting_futures_targets', None)
        
        step_summary = MessageFormatter.futures_registration_step(6, trade)
        
        await update.message.reply_text(
            step_summary + "\n\n"
            "✅ **Alvos configurados:**\n"
            f"{targets_summary}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ **Etapa 7/9 concluída!**\n\n"
            "📝 **Etapa 8/9 - Timeframe**\n\n"
            "Qual **timeframe** você usou para analisar a operação?\n"
            "_Isso ajuda a identificar suportes e resistências_",
            reply_markup=KeyboardBuilder.futures_timeframe_selection(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # Ask for more targets
        remaining = 100 - total_percent
        trade['target_count'] = target_count + 1
        
        await update.message.reply_text(
            f"✅ Alvo {target_count} adicionado!\n\n"
            f"**Alvos configurados:**\n{targets_summary}\n"
            f"📊 Total: {total_percent:.0f}% | Restante: {remaining:.0f}%\n\n"
            f"Digite o **próximo alvo** ou clique em 'Concluir alvos':",
            reply_markup=KeyboardBuilder.futures_targets_options(),
            parse_mode=ParseMode.MARKDOWN
        )


async def handle_futures_timeframe_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle timeframe input - Step 7 of new trade flow."""
    from src.utils.formatters import format_us_price, MessageFormatter
    
    timeframe = text.strip().lower()
    
    # Validate timeframe format
    valid_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
    if timeframe not in valid_timeframes:
        # Try to parse
        if timeframe.isdigit():
            timeframe = f"{timeframe}m"
        elif not any(timeframe.endswith(s) for s in ['m', 'h', 'd', 'w']):
            timeframe = f"{timeframe}h"
    
    context.user_data['futures_trade']['timeframe'] = timeframe
    context.user_data['futures_trade']['step'] = 7
    context.user_data.pop('awaiting_futures_timeframe', None)
    
    trade = context.user_data['futures_trade']
    pair = trade.get('pair', '???')
    side = trade.get('side', 'long')
    
    # Final step - show full summary and calculate risk
    step_summary = MessageFormatter.futures_registration_step(8, trade)
    
    await update.message.reply_text(
        step_summary + "\n\n"
        f"✅ **Etapa 8/9 concluída!**\n\n"
        "📝 **Etapa 9/9 - Cálculo de Risco e Confirmação**\n\n"
        f"🔍 Analisando suportes e resistências para {pair} no timeframe {timeframe.upper()}...",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Show zone check option
    await update.message.reply_text(
        f"🔍 **Deseja verificar zonas de suporte/resistência?**\n\n"
        f"Com base no timeframe {timeframe.upper()}, o bot pode sugerir:\n"
        f"• {'Resistências e zonas de stop (SHORT)' if side == 'short' else 'Suportes e zonas de stop (LONG)'}\n"
        f"• Ajustes no stop loss baseados em zonas técnicas\n\n"
        f"Isso ajuda a posicionar o stop em zonas mais seguras.",
        reply_markup=KeyboardBuilder.futures_zone_check(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_stop_percent_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle user's stop loss percentage input - Legacy flow."""
    from src.services.risk_management import risk_service
    context.user_data.pop('awaiting_futures_stop_percent', None)
    
    trade = context.user_data.get('futures_trade', {})
    pair = trade.get('pair', '???')
    timeframe = trade.get('timeframe', '4h')
    
    await update.message.reply_text(
        f"✅ Timeframe: **{timeframe.upper()}**\n\n"
        f"🔍 **Deseja verificar zona de liquidez/suporte?**\n\n"
        f"O bot pode analisar suportes e resistências com base nos últimos pivôs de preço.\n\n"
        f"Isso ajuda a posicionar o stop em zonas mais seguras.",
        reply_markup=KeyboardBuilder.futures_zone_check(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_quantity_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle futures quantity input."""
    try:
        quantity = float(text.replace(',', '.'))
        if quantity <= 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor, insira um número válido.\n\n"
            "Exemplo: `0.1` ou `100`",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    context.user_data['futures_trade']['quantity'] = quantity
    context.user_data.pop('awaiting_futures_quantity', None)
    context.user_data['awaiting_futures_margin'] = True
    
    pair = context.user_data['futures_trade'].get('pair', '???')
    entry_price = context.user_data['futures_trade'].get('entry_price', 0)
    leverage = context.user_data['futures_trade'].get('leverage', 1)
    
    position_value = quantity * entry_price
    suggested_margin = position_value / leverage
    
    await update.message.reply_text(
        f"📝 **Trade: {pair}** {leverage}x\n\n"
        f"📥 Entry: ${entry_price:,.4f}\n"
        f"📦 Quantidade: {quantity:,.6f}\n"
        f"📊 Valor da posição: ${position_value:,.2f}\n\n"
        f"Digite a **margem** (colateral) em USD:\n\n"
        f"💡 Sugestão: ${suggested_margin:,.2f}",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_margin_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle futures margin input (valor investido) - Step 3 of new trade flow."""
    from src.utils.formatters import format_us_price, parse_us_number, MessageFormatter
    
    try:
        margin = parse_us_number(text)
        if margin <= 0:
            raise ValueError()
    except:
        await update.message.reply_text(
            "❌ Por favor, insira um número válido.\n\n"
            "Exemplo: `100`, `500.50` ou `1,000.00`",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    trade = context.user_data['futures_trade']
    entry_price = trade.get('entry_price', 0)
    futures_balance = trade.get('futures_balance', 0)
    
    # Calculate allocation percentage
    allocation_percent = (margin / futures_balance * 100) if futures_balance > 0 else 0
    
    context.user_data['futures_trade']['margin'] = margin
    context.user_data['futures_trade']['allocation_percent'] = allocation_percent
    context.user_data['futures_trade']['step'] = 3
    context.user_data.pop('awaiting_futures_margin', None)
    
    step_summary = MessageFormatter.futures_registration_step(3, trade)
    
    is_altcoin = trade.get('is_altcoin', False)
    altcoin_warning = ""
    if is_altcoin:
        altcoin_warning = "\n⚠️ **ATENÇÃO:** Este é um altcoin. Alavancagem >3x é arriscada!\n"
    
    await update.message.reply_text(
        step_summary + "\n\n"
        f"💵 **Valor Investido:** U$ {format_us_price(margin)}\n"
        f"📈 **Alocação:** {allocation_percent:.2f}% da carteira\n"
        f"{altcoin_warning}"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ **Etapa 3/9 concluída!**\n\n"
        "📝 **Etapa 4/9 - Direção**\n\n"
        "A operação será **LONG** (compra/alta) ou **SHORT** (venda/baixa)?",
        reply_markup=KeyboardBuilder.futures_side_selection(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_close_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle futures close price input."""
    try:
        price = float(text.replace(',', '.').replace('$', ''))
        if price <= 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor, insira um número válido.\n\n"
            "Exemplo: `67500` ou `0.6123`",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    trade_id = context.user_data.get('futures_close_trade_id')
    context.user_data['futures_close_price'] = price
    
    # Get trade info to calculate P&L preview
    async with get_async_session() as session:
        futures_repo = FuturesRepository(session)
        trade = await futures_repo.get_by_id(trade_id)
    
    if not trade:
        await update.message.reply_text(
            "❌ Trade não encontrado.",
            reply_markup=KeyboardBuilder.futures_menu()
        )
        return
    
    # Calculate preview P&L
    price_diff = price - trade.entry_price
    if trade.side == "short":
        price_diff = -price_diff
    
    pnl = price_diff * trade.quantity * trade.leverage
    pnl_pct = (price_diff / trade.entry_price) * 100 * trade.leverage if trade.entry_price > 0 else 0
    pnl_emoji = "🟢" if pnl >= 0 else "🔴"
    
    await update.message.reply_text(
        f"📤 **Confirmar Fechamento**\n\n"
        f"🪙 **{trade.pair}** @ {trade.leverage}x\n"
        f"📥 Entry: ${trade.entry_price:,.4f}\n"
        f"📤 Exit: ${price:,.4f}\n\n"
        f"{pnl_emoji} **P/L Previsto:** ${pnl:+,.2f} ({pnl_pct:+.2f}%)\n\n"
        f"Confirma o fechamento?",
        reply_markup=KeyboardBuilder.futures_close_confirm(trade_id),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_sltp_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle futures stop loss / take profit input."""
    parts = text.split()
    
    if len(parts) != 2:
        await update.message.reply_text(
            "❌ Formato inválido.\n\n"
            "Use: `stop_loss take_profit`\n"
            "Exemplo: `64000 72000`\n"
            "Para pular um valor, use `0`",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        stop_loss = float(parts[0].replace(',', '.').replace('$', ''))
        take_profit = float(parts[1].replace(',', '.').replace('$', ''))
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor, insira números válidos.\n\n"
            "Exemplo: `64000 72000`",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    trade_id = context.user_data.get('futures_sltp_trade_id')
    user = update.effective_user
    
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        futures_repo = FuturesRepository(session)
        
        db_user = await user_repo.get_by_telegram_id(user.id)
        if not db_user:
            await update.message.reply_text(
                "❌ Usuário não encontrado.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        trade = await futures_repo.get_by_id(trade_id)
        if not trade or trade.user_id != db_user.id:
            await update.message.reply_text(
                "❌ Trade não encontrado.",
                reply_markup=KeyboardBuilder.futures_menu()
            )
            return
        
        updates = {}
        if stop_loss > 0:
            updates['stop_loss'] = stop_loss
        if take_profit > 0:
            updates['take_profit'] = take_profit
        
        if updates:
            await futures_repo.update_trade(trade_id, **updates)
            await session.commit()
    
    context.user_data.pop('awaiting_futures_sltp', None)
    context.user_data.pop('futures_sltp_trade_id', None)
    
    result = []
    if stop_loss > 0:
        result.append(f"🛑 Stop Loss: ${stop_loss:,.4f}")
    if take_profit > 0:
        result.append(f"🎯 Take Profit: ${take_profit:,.4f}")
    
    await update.message.reply_text(
        f"✅ **SL/TP Atualizados!**\n\n" + "\n".join(result),
        reply_markup=KeyboardBuilder.futures_trade_actions(trade_id),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_trend_symbol_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle user input for trend analysis symbol."""
    symbol = text.strip().upper()
    
    # Clean symbol
    symbol = symbol.replace("USDT", "").replace("USD", "").replace("/", "")
    
    if not symbol or len(symbol) < 2:
        await update.message.reply_text(
            "❌ Símbolo inválido. Por favor, digite um símbolo válido.\n"
            "Exemplo: `BTC`, `ETH`, `SOL`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    context.user_data.pop('awaiting', None)
    
    # Create timeframe selection keyboard
    keyboard = [
        [
            InlineKeyboardButton("1h", callback_data=f"trend_run_{symbol}_1h"),
            InlineKeyboardButton("4h ⭐", callback_data=f"trend_run_{symbol}_4h"),
            InlineKeyboardButton("1d ⭐", callback_data=f"trend_run_{symbol}_1d"),
        ],
        [InlineKeyboardButton("🔙 Voltar", callback_data="trend_analysis_menu")],
    ]
    
    await update.message.reply_text(
        f"📊 **Analisar {symbol}**\n\n"
        "Selecione o timeframe:\n\n"
        "⭐ 4h e 1d são os mais confiáveis",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
