"""
Handlers para o módulo Gorni Strategies.

Fornece comando /estrategias e callbacks isolados (pattern gg_*).
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from src.services.gurugorni_strategies import (
    get_strategy_manager,
    STRATEGY_DESCRIPTIONS,
    ActionType,
    StrategySignal,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# COMANDO /estrategias
# ============================================================================

async def estrategias_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o comando /estrategias - mostra menu de estratégias Gorni."""
    manager = get_strategy_manager()
    user_id = update.effective_user.id
    
    keyboard = _build_strategies_menu(manager, user_id)
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        "🧠 <b>Estratégias Gorni</b>\n\n"
        "<i>Sistema completo validado com backtesting (2022-2026)</i>\n\n"
        "✅ = Alerta ativo  |  ⭕ = Alerta inativo\n\n"
        "<b>Selecione uma estratégia:</b>"
    )
    
    await update.message.reply_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )


def _build_strategies_menu(manager, user_id: int) -> list:
    """Constrói teclado do menu de estratégias."""
    keyboard = []
    
    for key, strategy in manager.strategies.items():
        is_active = manager.is_alert_active(user_id, key)
        status = "✅" if is_active else "⭕"
        button_text = f"{status} {strategy.emoji} {strategy.name} ({strategy.accuracy}%)"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"gg_strat_{key}")])
    
    keyboard.append([InlineKeyboardButton("📊 Comparar Estratégias", callback_data="gg_compare")])
    keyboard.append([InlineKeyboardButton("❓ Como Funciona", callback_data="gg_how")])
    keyboard.append([InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")])
    
    return keyboard


# ============================================================================
# CALLBACK HANDLER (pattern gg_*)
# ============================================================================

async def estrategias_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para callbacks das estratégias Gorni (pattern gg_*)."""
    query = update.callback_query
    await query.answer()
    
    manager = get_strategy_manager()
    user_id = query.from_user.id
    data = query.data
    
    try:
        if data == "gg_menu":
            await _handle_menu(query, manager, user_id)
        
        elif data.startswith("gg_strat_"):
            strategy_key = data.replace("gg_strat_", "")
            await _handle_strategy_detail(query, manager, user_id, strategy_key)
        
        elif data.startswith("gg_toggle_"):
            strategy_key = data.replace("gg_toggle_", "")
            await _handle_toggle_alert(query, context, manager, user_id, strategy_key)
        
        elif data == "gg_compare":
            await _handle_compare(query)
        
        elif data == "gg_how":
            await _handle_how_it_works(query)
        
        elif data == "gg_close":
            await query.message.delete()
            
    except Exception as e:
        logger.error(f"Erro no callback gg_*: {e}")
        await query.edit_message_text(
            "❌ Erro ao processar ação. Tente novamente.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar", callback_data="gg_menu")
            ]])
        )


async def _handle_menu(query, manager, user_id: int):
    """Mostra menu principal de estratégias."""
    keyboard = _build_strategies_menu(manager, user_id)
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        "🧠 <b>Estratégias Gorni</b>\n\n"
        "<i>Sistema completo validado com backtesting (2022-2026)</i>\n\n"
        "✅ = Alerta ativo  |  ⭕ = Alerta inativo\n\n"
        "<b>Selecione uma estratégia:</b>"
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )


async def _handle_strategy_detail(query, manager, user_id: int, strategy_key: str):
    """Mostra detalhes de uma estratégia."""
    strategy = manager.strategies.get(strategy_key)
    
    if not strategy:
        await query.edit_message_text(
            "❌ Estratégia não encontrada.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar", callback_data="gg_menu")
            ]])
        )
        return
    
    is_active = manager.is_alert_active(user_id, strategy_key)
    description = STRATEGY_DESCRIPTIONS.get(strategy_key, "")
    
    message = (
        f"{strategy.emoji} <b>{strategy.name}</b>\n\n"
        f"<b>Acurácia Validada:</b> {strategy.accuracy}%\n"
        f"<b>Foco:</b> {strategy.focus}\n"
        f"<b>Status:</b> {'✅ Ativo' if is_active else '⭕ Inativo'}\n\n"
        f"<b>🔍 O que faz:</b>\n{description}\n\n"
        "⚠️ <i>A lógica interna é proprietária.</i>\n"
        "Você receberá apenas sinais e probabilidade."
    )
    
    keyboard = [
        [InlineKeyboardButton(
            "❌ Desativar Alerta" if is_active else "✅ Ativar Alerta",
            callback_data=f"gg_toggle_{strategy_key}"
        )],
        [InlineKeyboardButton("🔙 Voltar", callback_data="gg_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )


async def _handle_toggle_alert(query, context, manager, user_id: int, strategy_key: str):
    """Ativa/desativa alerta de uma estratégia."""
    is_active = manager.is_alert_active(user_id, strategy_key)
    
    if is_active:
        manager.deactivate_alert(user_id, strategy_key)
        await query.answer("❌ Alerta desativado")
    else:
        manager.activate_alert(user_id, strategy_key)
        await query.answer("✅ Alerta ativado!")
    
    # Recarrega a tela de detalhes da estratégia
    await _handle_strategy_detail(query, manager, user_id, strategy_key)


async def _handle_compare(query):
    """Mostra comparação entre estratégias."""
    message = (
        "📊 <b>COMPARAÇÃO DE ESTRATÉGIAS</b>\n\n"
        "<b>🛡️ Gorni Shadow</b>\n"
        "• Acurácia: <b>85%</b> ⭐⭐⭐⭐⭐\n"
        "• Foco: Proteção contra quedas\n"
        "• Timeframe: 1H - 1D\n"
        "• Melhor para: Evitar perdas\n\n"
        "<b>🎯 Gorni Reversal Hunter</b>\n"
        "• Acurácia: <b>82%</b> ⭐⭐⭐⭐\n"
        "• Foco: Compras no fundo\n"
        "• Timeframe: 4H - 1W\n"
        "• Melhor para: Acumulação\n\n"
        "<b>⚡ Gorni Momentum Rider</b>\n"
        "• Acurácia: <b>78%</b> ⭐⭐⭐⭐\n"
        "• Foco: Surfar tendências\n"
        "• Timeframe: 1H - 3D\n"
        "• Melhor para: Swing trade\n\n"
        "<b>⚔️ Gorni Flash Scalper</b>\n"
        "• Acurácia: <b>71%</b> ⭐⭐⭐\n"
        "• Foco: Micro-movimentos\n"
        "• Timeframe: 5m - 1H\n"
        "• Melhor para: Scalping (experientes)\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>💡 RECOMENDAÇÃO:</b>\n"
        "Combine múltiplas estratégias para máxima efetividade!\n\n"
        "• <b>Conservador:</b> Shadow + Reversal\n"
        "• <b>Moderado:</b> Shadow + Momentum\n"
        "• <b>Agressivo:</b> Todas as 4"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data="gg_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )


async def _handle_how_it_works(query):
    """Mostra explicação de como funcionam as estratégias."""
    message = (
        "❓ <b>Como Funcionam as Estratégias Gorni</b>\n\n"
        "<b>1. 📊 Backtesting Validado</b>\n"
        "Todas as estratégias foram validadas com dados reais\n"
        "de 2022 a 2026, incluindo bear e bull markets.\n\n"
        "<b>2. 🔍 Detecção de Padrões</b>\n"
        "Analisam múltiplos indicadores simultaneamente:\n"
        "• Movimentos de baleias\n"
        "• Liquidações em massa\n"
        "• Métricas on-chain (SOPR, NUPL)\n"
        "• Indicadores técnicos (RSI, MAs)\n"
        "• Fear & Greed Index\n"
        "• Order book e volume\n\n"
        "<b>3. 🔔 Alertas Inteligentes</b>\n"
        "Quando um padrão é detectado, você recebe:\n"
        "• Código do padrão (ex: GGS-1234)\n"
        "• Probabilidade de acerto\n"
        "• Ação recomendada\n"
        "• Alvo e Stop (quando aplicável)\n\n"
        "<b>⚠️ IMPORTANTE:</b>\n"
        "• Use sempre gestão de risco adequada\n"
        "• Nenhuma estratégia é 100% precisa\n"
        "• A lógica interna é <b>proprietária</b>\n"
        "• Nunca arrisque mais do que pode perder\n\n"
        "<b>🔒 Segurança:</b>\n"
        "Os algoritmos internos são confidenciais.\n"
        "Você recebe apenas os sinais resultantes."
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data="gg_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )


# ============================================================================
# FUNÇÃO PARA ENVIAR ALERTAS DE ESTRATÉGIA
# ============================================================================

async def send_strategy_alert(context: ContextTypes.DEFAULT_TYPE, user_id: int, signal: StrategySignal):
    """Envia alerta de estratégia para um usuário."""
    action_emoji = {
        ActionType.BUY: "🟢",
        ActionType.SELL: "🔴",
        ActionType.ACCUMULATE: "🔵",
        ActionType.PROTECT: "🛡️",
        ActionType.HOLD: "⏸️",
        ActionType.SCALP: "⚔️"
    }
    
    emoji = action_emoji.get(signal.action, "🔔")
    
    message = (
        f"🔔 <b>Alerta: {signal.strategy_name}</b>\n\n"
        f"<b>Padrão:</b> <code>{signal.pattern_code}</code>\n"
        f"<b>Probabilidade:</b> {signal.confidence:.0f}%\n"
        f"<b>Ação:</b> {emoji} {signal.action.value.upper()}\n"
        f"<b>Preço:</b> ${signal.price:,.2f}\n"
        f"<b>Timeframe:</b> {signal.timeframe}\n"
    )
    
    if signal.target_price:
        message += f"<b>Alvo:</b> ${signal.target_price:,.2f}\n"
    if signal.stop_loss:
        message += f"<b>Stop:</b> ${signal.stop_loss:,.2f}\n"
    
    if signal.reasons:
        message += "\n<b>Indicadores:</b>\n"
        for reason in signal.reasons[:4]:
            message += f"• {reason}\n"
    
    message += (
        "\n⚠️ <b>Use gestão de risco adequada</b>\n\n"
        "<i>🔒 Padrão proprietário - lógica não divulgada</i>"
    )
    
    keyboard = [[InlineKeyboardButton("📊 Ver Estratégias", callback_data="gg_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        logger.info(f"Alerta de estratégia enviado para {user_id}: {signal.strategy_name}")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar alerta para {user_id}: {e}")
        return False


# ============================================================================
# FUNÇÃO PARA ANALISAR MERCADO E ENVIAR ALERTAS
# ============================================================================

async def check_market_and_send_alerts(context: ContextTypes.DEFAULT_TYPE, market_data: dict):
    """
    Analisa mercado com as 4 estratégias e envia alertas aos usuários.
    
    Esta função deve ser chamada periodicamente (ex: a cada 5 minutos).
    """
    manager = get_strategy_manager()
    signals = manager.analyze_market(market_data)
    
    alerts_sent = 0
    
    for signal in signals:
        # Encontra a key da estratégia
        strategy_key = None
        for key, strategy in manager.strategies.items():
            if strategy.name == signal.strategy_name:
                strategy_key = key
                break
        
        if not strategy_key:
            continue
        
        # Envia para todos os usuários com alerta ativo
        users = manager.get_active_users_for_strategy(strategy_key)
        for user_id in users:
            success = await send_strategy_alert(context, user_id, signal)
            if success:
                alerts_sent += 1
    
    if alerts_sent > 0:
        logger.info(f"Enviados {alerts_sent} alertas de estratégias Gorni")
    
    return alerts_sent


# Export public API
__all__ = [
    'estrategias_command',
    'estrategias_callback',
    'send_strategy_alert',
    'check_market_and_send_alerts',
]
