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

logger = get_logger(__name__)

# Major coins (not altcoins)
MAJOR_COINS = {"BTC", "ETH", "BNB"}


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
    elif context.user_data.get('awaiting_futures_stop_percent'):
        await handle_futures_stop_percent_input(update, context, text)
        return
    elif context.user_data.get('awaiting_futures_margin_for_risk'):
        await handle_futures_margin_for_risk_input(update, context, text)
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
    try:
        price = float(text.replace(',', '.').replace('$', ''))
        if price <= 0:
            raise ValueError("Price must be positive")
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor, insira um número válido para o preço.\n\n"
            "Exemplo: `0.00001`, `50000`, `1.5`",
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
        f"📊 **Preço Atual:** ${current_price:,.6f}\n"
        f"💵 **Preço de Compra:** ${price:,.6f}\n\n"
        f"\u2796\u2796\u2796\u2796\u2796\u2796\u2796\u2796\u2796\u2796\n\n"
        f"💸 **Passo 2/2:** Digite o **valor total investido** (em USD):",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_total_invested_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle total invested input when adding an asset."""
    try:
        total_invested = float(text.replace(',', '.').replace('$', ''))
        if total_invested <= 0:
            raise ValueError("Total must be positive")
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor, insira um número válido para o total investido.\n\n"
            "Exemplo: `100`, `1500.50`, `25000`",
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
    
    # Calculate current value and profit/loss
    current_value = quantity * current_price
    profit_loss = current_value - total_invested
    profit_percent = (profit_loss / total_invested * 100) if total_invested > 0 else 0
    pl_emoji = "🟢" if profit_loss >= 0 else "🔴"
    
    # Show confirmation with option to correct
    message = (
        f"📋 **Resumo do Ativo**\n\n"
        f"🪙 **{symbol.upper()}** ({name})\n\n"
        f"💵 **Preço de Compra:** ${price:,.6f}\n"
        f"💸 **Total Investido:** ${total_invested:,.2f}\n"
        f"📦 **Quantidade:** {quantity:,.6f} _(calculado)_\n\n"
        f"\u2796\u2796\u2796\u2796\u2796\u2796\u2796\u2796\u2796\u2796\n\n"
        f"📊 **Preço Atual:** ${current_price:,.6f}\n"
        f"📈 **Valorização do investimento inicial:** ${current_value:,.2f}\n"
        f"{pl_emoji} **Lucro/Prejuízo:** ${profit_loss:,.2f} ({profit_percent:+.2f}%)\n\n"
        f"Confirma ou deseja corrigir algum dado?"
    )
    
    await update.message.reply_text(
        message,
        reply_markup=KeyboardBuilder.confirm_or_correct_asset(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_entry_quantity_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle quantity input for new entry."""
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
    
    context.user_data['entry_quantity'] = quantity
    context.user_data['state'] = 'waiting_entry_price'
    
    await update.message.reply_text(
        f"📦 **Quantidade:** {quantity}\n\n"
        "Agora digite o **preço de compra** (em USD) desta entrada:",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_entry_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle price input for new entry."""
    try:
        price = float(text.replace(',', '.').replace('$', ''))
        if price <= 0:
            raise ValueError("Price must be positive")
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor, insira um número válido para o preço.",
            reply_markup=KeyboardBuilder.cancel_action()
        )
        return
    
    user = update.effective_user
    asset_id = context.user_data.get('entry_asset_id')
    quantity = context.user_data.get('entry_quantity')
    
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
        
        # Create new entry
        total_value = quantity * price
        await entry_repo.create_entry(
            asset_id=asset_id,
            entry_price=price,
            quantity=quantity,
            total_value=total_value,
            notes=f"Entrada em {datetime.now().strftime('%d/%m/%Y')}"
        )
        
        # Update asset total quantity
        new_quantity = asset.quantity + quantity
        await asset_repo.update_asset(asset_id, quantity=new_quantity)
        
        # Get updated asset
        asset = await asset_repo.get_by_id(asset_id)
    
    context.user_data.clear()
    
    await update.message.reply_text(
        f"✅ **Nova Entrada Adicionada!**\n\n"
        f"🪙 **{asset.symbol.upper()}**\n\n"
        f"📦 **Quantidade adicionada:** {quantity:,.6f}\n"
        f"💰 **Preço de compra:** ${price:,.6f}\n"
        f"💵 **Valor total:** ${total_value:,.2f}\n\n"
        f"📊 **Quantidade total:** {asset.quantity:,.6f}\n"
        f"📈 **Preço médio:** ${asset.average_price:,.6f}",
        reply_markup=KeyboardBuilder.asset_actions(asset_id),
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
    try:
        price = float(text.replace(',', '.').replace('$', ''))
        if price <= 0:
            raise ValueError("Price must be positive")
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor, insira um número válido para o preço.",
            reply_markup=KeyboardBuilder.cancel_action()
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
    """Handle futures pair symbol input - Step 1 of new trade flow."""
    from src.services.risk_management import risk_service
    
    pair_input = text.upper().strip().replace("/", "").replace("-", "")
    user = update.effective_user
    
    # Check if user provided full pair or just base symbol
    quote_currencies = ["USDT", "USDC", "USD", "BTC", "ETH", "BNB", "BUSD"]
    
    has_quote = any(pair_input.endswith(q) for q in quote_currencies)
    
    if has_quote:
        pair = pair_input
        for q in quote_currencies:
            if pair_input.endswith(q):
                symbol = pair_input[:-len(q)]
                break
    else:
        symbol = pair_input
        pair = f"{symbol}USDT"
    
    # Check if it's a valid symbol using TradingView
    await update.message.reply_text("🔍 Verificando par e analisando gerenciamento de risco...")
    
    tv = TradingViewService()
    try:
        price_data = await tv.get_price(symbol)
    finally:
        await tv.close()
    
    if not price_data:
        await update.message.reply_text(
            f"❌ Não foi possível encontrar o par {pair}.\n\n"
            "Verifique o símbolo e tente novamente.\n"
            "Exemplos: `BTCUSDT`, `ETHUSDT`, `SOL`, `DOGE`",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    is_altcoin = symbol not in MAJOR_COINS
    current_price = price_data.get('price', 0)
    
    # Get user's futures balance and risk config
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        futures_repo = FuturesRepository(session)
        
        db_user = await user_repo.get_by_telegram_id(user.id)
        futures_balance = db_user.futures_balance or 0
        risk_percent = db_user.futures_risk_percent or 5.0
        
        # Get total open risk
        open_risk = await futures_repo.get_total_open_risk(db_user.id)
    
    # Store trade data
    context.user_data['futures_trade'] = {
        'pair': pair,
        'symbol': symbol,
        'is_altcoin': is_altcoin,
        'current_price': current_price,
        'futures_balance': futures_balance,
        'risk_percent': risk_percent,
        'open_risk': open_risk,
        'user_id': db_user.id
    }
    context.user_data.pop('awaiting_futures_pair', None)
    
    # Calculate available risk
    max_risk = futures_balance * (risk_percent / 100)
    available_risk = max_risk - open_risk
    
    altcoin_warning = ""
    if is_altcoin:
        altcoin_warning = "\n⚠️ **ATENÇÃO:** Este é um altcoin. Alavancagem >3x é arriscada!"
    
    balance_msg = ""
    if futures_balance > 0:
        balance_msg = (
            f"\n\n💰 **Carteira de Futuros:** ${futures_balance:,.2f}\n"
            f"⚙️ **Risco configurado:** {risk_percent}% por trade\n"
            f"💵 **Risco máximo:** ${max_risk:,.2f}\n"
            f"🔒 **Risco em uso:** ${open_risk:,.2f}\n"
            f"✅ **Disponível:** ${available_risk:,.2f}"
        )
    else:
        balance_msg = (
            f"\n\n⚠️ **Atenção:** Sua carteira de futuros está em $0.\n"
            f"Configure seu saldo em Configurações > Saldo de Futuros"
        )
    
    await update.message.reply_text(
        f"📝 **Par selecionado: {pair}**\n\n"
        f"💰 Preço atual: ${current_price:,.4f}\n"
        f"{altcoin_warning}"
        f"{balance_msg}\n\n"
        "Selecione a **direção** do trade:",
        reply_markup=KeyboardBuilder.futures_side_selection(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_futures_entry_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle futures entry price input - Step 3 of new trade flow."""
    from src.services.risk_management import risk_service
    
    try:
        price = float(text.replace(',', '.').replace('$', ''))
        if price <= 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor, insira um número válido.\n\n"
            "Exemplo: `65000` ou `0.5432`",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    context.user_data['futures_trade']['entry_price'] = price
    context.user_data.pop('awaiting_futures_entry', None)
    
    trade = context.user_data['futures_trade']
    pair = trade.get('pair', '???')
    side = trade.get('side', 'long')
    leverage = trade.get('leverage', 1)
    futures_balance = trade.get('futures_balance', 0)
    risk_percent = trade.get('risk_percent', 5.0)
    open_risk = trade.get('open_risk', 0)
    
    # Calculate risk parameters
    if futures_balance > 0:
        risk_calc = risk_service.calculate_risk(
            futures_balance=futures_balance,
            risk_percent=risk_percent,
            entry_price=price,
            leverage=leverage,
            direction=side,
            open_positions_risk=open_risk
        )
        
        context.user_data['futures_trade']['risk_calc'] = risk_calc
        
        # Show risk analysis and ask for margin
        risk_msg = risk_service.format_risk_summary(risk_calc, price, leverage, side)
        
        await update.message.reply_text(
            risk_msg + "\n\n"
            "💰 **Qual a MARGEM (aporte) deste trade?**\n\n"
            "Digite o valor em USD que será usado como colateral:\n\n"
            f"💡 _Sugestão baseada no risco: ${risk_calc.max_risk_usd:,.2f}_",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        
        context.user_data['awaiting_futures_margin_for_risk'] = True
    else:
        # No balance configured, use old flow
        context.user_data['awaiting_futures_quantity'] = True
        
        await update.message.reply_text(
            f"📝 **Trade: {pair}** {leverage}x @ ${price:,.4f}\n\n"
            "Digite a **quantidade** de moedas:\n\n"
            "Exemplo: `0.1` para 0.1 BTC",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )


async def handle_futures_margin_for_risk_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle margin input for risk calculation - Step between entry and stop %."""
    from src.services.risk_management import risk_service
    
    try:
        margin = float(text.replace(',', '.').replace('$', ''))
        if margin <= 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor, insira um número válido.\n\n"
            "Exemplo: `100` ou `500.50`",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    context.user_data['futures_trade']['margin'] = margin
    context.user_data.pop('awaiting_futures_margin_for_risk', None)
    
    trade = context.user_data['futures_trade']
    entry_price = trade.get('entry_price', 0)
    side = trade.get('side', 'long')
    leverage = trade.get('leverage', 1)
    risk_calc = trade.get('risk_calc')
    
    # Calculate position size based on margin
    position_value = margin * leverage
    quantity = position_value / entry_price if entry_price > 0 else 0
    context.user_data['futures_trade']['quantity'] = quantity
    
    # Calculate suggested stop % based on margin and max risk
    max_risk = risk_calc.max_risk_usd if risk_calc else margin * 0.05
    # suggested_stop = (max_risk / position_value) * 100
    suggested_stop = (max_risk / position_value) * 100 if position_value > 0 else 2.0
    suggested_stop = min(suggested_stop, 10.0)  # Cap at 10%
    
    await update.message.reply_text(
        f"✅ **Margem definida: ${margin:,.2f}**\n"
        f"📊 Posição total: ${position_value:,.2f}\n"
        f"📦 Quantidade: {quantity:,.6f}\n\n"
        f"❓ **Qual % de stop você quer usar?**\n\n"
        f"Digite o percentual de distância do stop (ex: `2.5` para 2.5%):\n\n"
        f"💡 _Sugerido: {suggested_stop:.2f}% = perda máx ${(position_value * suggested_stop / 100):,.2f}_",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )
    
    context.user_data['awaiting_futures_stop_percent'] = True


async def handle_futures_stop_percent_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle user's stop loss percentage input - Step 4 of new trade flow."""
    from src.services.risk_management import risk_service
    
    try:
        stop_pct = float(text.replace(',', '.').replace('%', ''))
        if stop_pct <= 0 or stop_pct > 50:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor, insira um percentual válido (0.1 a 50).\n\n"
            "Exemplo: `2.5` para 2.5%",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    context.user_data.pop('awaiting_futures_stop_percent', None)
    
    trade = context.user_data['futures_trade']
    entry_price = trade.get('entry_price', 0)
    side = trade.get('side', 'long')
    leverage = trade.get('leverage', 1)
    margin = trade.get('margin', 0)  # Use margin instead of futures_balance
    risk_calc = trade.get('risk_calc')
    
    # Calculate stop loss details using margin
    stop_calc = risk_service.calculate_stop_loss(
        entry_price=entry_price,
        stop_percent=stop_pct,
        direction=side,
        leverage=leverage,
        margin=margin,  # Now using actual trade margin
        max_risk_usd=risk_calc.max_risk_usd if risk_calc else margin,
        available_risk_usd=risk_calc.available_risk_usd if risk_calc else margin
    )
    
    context.user_data['futures_trade']['stop_percent'] = stop_pct
    context.user_data['futures_trade']['stop_price'] = stop_calc.stop_price
    context.user_data['futures_trade']['risk_usd'] = stop_calc.risk_usd
    context.user_data['futures_trade']['stop_calc'] = stop_calc
    
    # Check if risk exceeds available
    if stop_calc.risk_usd > (risk_calc.available_risk_usd if risk_calc else float('inf')):
        await update.message.reply_text(
            f"⚠️ **Risco Excede Disponível!**\n\n"
            f"• Risco calculado: ${stop_calc.risk_usd:,.2f}\n"
            f"• Disponível: ${risk_calc.available_risk_usd:,.2f}\n\n"
            f"Reduza o % de stop ou feche outras posições.\n\n"
            f"Digite um novo % de stop:",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data['awaiting_futures_stop_percent'] = True
        return
    
    stop_msg = risk_service.format_stop_choice(stop_calc, risk_calc.max_risk_usd if risk_calc else stop_calc.risk_usd)
    
    await update.message.reply_text(
        stop_msg + "\n\n"
        "📊 **Qual timeframe você usou para analisar?**\n\n"
        "Digite o timeframe (ex: `15m`, `1h`, `4h`, `1d`):",
        reply_markup=KeyboardBuilder.cancel_action(),
        parse_mode=ParseMode.MARKDOWN
    )
    
    context.user_data['awaiting_futures_timeframe'] = True


async def handle_futures_timeframe_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle timeframe input - Step 5 of new trade flow."""
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
    context.user_data.pop('awaiting_futures_timeframe', None)
    
    trade = context.user_data['futures_trade']
    pair = trade.get('pair', '???')
    side = trade.get('side', 'long')
    
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
    """Handle futures margin input and show confirmation."""
    try:
        margin = float(text.replace(',', '.').replace('$', ''))
        if margin <= 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor, insira um número válido.\n\n"
            "Exemplo: `100` ou `500.50`",
            reply_markup=KeyboardBuilder.cancel_action(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    context.user_data['futures_trade']['margin'] = margin
    context.user_data.pop('awaiting_futures_margin', None)
    
    trade = context.user_data['futures_trade']
    pair = trade.get('pair', '???')
    side = trade.get('side', 'long')
    leverage = trade.get('leverage', 1)
    entry_price = trade.get('entry_price', 0)
    quantity = trade.get('quantity', 0)
    is_altcoin = trade.get('is_altcoin', False)
    
    # Check if high risk
    show_risk_warning = (leverage > 3 and is_altcoin) or leverage >= 10
    
    message = MessageFormatter.futures_new_trade_summary(
        pair=pair,
        side=side,
        leverage=leverage,
        entry_price=entry_price,
        quantity=quantity,
        margin=margin,
        is_altcoin=is_altcoin
    )
    
    await update.message.reply_text(
        message,
        reply_markup=KeyboardBuilder.futures_confirm_trade(show_risk_warning),
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
