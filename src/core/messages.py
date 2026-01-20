"""
Message templates for the Crypto Portfolio Bot.

This module centralizes all user-facing text messages to:
1. Make translations easier (i18n preparation)
2. Keep messages consistent across the application
3. Allow easy modification of text without code changes

Usage:
    from src.core.messages import MSG
    
    text = MSG.USER_NOT_FOUND
    text = MSG.ASSET_ADDED.format(symbol="BTC", quantity=1.5)
"""

class Messages:
    """Centralized message templates for the bot."""
    
    # ==========================================================================
    # ERROR MESSAGES
    # ==========================================================================
    
    USER_NOT_FOUND = "❌ Usuário não encontrado. Use /start para começar."
    ASSET_NOT_FOUND = "❌ Ativo não encontrado."
    TRADE_NOT_FOUND = "❌ Trade não encontrado."
    SESSION_EXPIRED = "❌ Sessão expirada. Inicie novamente."
    ACTION_NOT_RECOGNIZED = "❌ Ação não reconhecida."
    INCOMPLETE_DATA = "❌ Dados incompletos. Por favor, tente novamente."
    INVALID_VALUE = "❌ Valor inválido. Por favor, digite um número válido."
    PROCESSING_ERROR = "❌ Erro ao processar ação: {error}"
    ANALYSIS_ERROR = "❌ Não foi possível analisar {symbol}."
    
    # ==========================================================================
    # SUCCESS MESSAGES
    # ==========================================================================
    
    ACTION_CANCELLED = "❌ Ação cancelada.\n\nUse o menu para continuar:"
    ASSET_ADDED = "✅ **Ativo adicionado com sucesso!**\n\n🪙 **{symbol}** ({name})\n📦 Quantidade: {quantity:,.6f}\n💰 Preço de compra: ${price:,.6f}\n💵 Total investido: ${total:,.2f}"
    ENTRY_ADDED = "✅ **Entrada adicionada!**\n\n🪙 **{symbol}**\n📦 Quantidade adicionada: {quantity:,.6f}\n💰 Preço: ${price:,.6f}\n💸 Investido: ${invested:,.2f}\n📊 Quantidade total: {total:,.6f}"
    ASSET_REMOVED = "✅ **{symbol}** removido com sucesso!"
    PRICES_UPDATED = "✅ Preços atualizados!"
    NOTIFICATIONS_TOGGLED = "✅ Notificações **{status}** com sucesso!"
    DEATH_CROSS_ALERTS_TOGGLED = "✅ Alertas de Death Cross **{status}** com sucesso!"
    
    # ==========================================================================
    # STATUS MESSAGES
    # ==========================================================================
    
    LOADING_PRICES = "⏳ Atualizando preços do TradingView..."
    LOADING_ANALYSIS = "⏳ Carregando análise técnica do TradingView..."
    SCANNING_DEATH_CROSS = "⏳ Escaneando ativos em Death Cross...\nIsso pode levar alguns segundos."
    SCANNING_GOLDEN_CROSS = "⏳ Escaneando ativos em Golden Cross...\nIsso pode levar alguns segundos."
    ANALYZING_ASSETS = "⏳ Analisando {count} ativos ({timeframe})...\nIsso pode levar alguns segundos."
    
    # ==========================================================================
    # INPUT PROMPTS
    # ==========================================================================
    
    PROMPT_COIN_SEARCH = (
        "🔍 **Adicionar Ativo**\n\n"
        "Digite o **nome** ou **símbolo** da criptomoeda:\n\n"
        "Exemplos: `BTC`, `ETH`, `SOL`, `ADA`"
    )
    
    PROMPT_SEARCH_COIN = (
        "🔍 **Buscar Moeda**\n\n"
        "Digite o **símbolo** da criptomoeda para ver informações:\n\n"
        "Exemplos: `BTC`, `ETH`, `SOL`"
    )
    
    PROMPT_PURCHASE_PRICE = (
        "💰 **Adicionar {symbol}**\n\n"
        "📊 **Preço Atual:** ${current_price:,.6f}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "💵 **Passo 1/2:** Digite o **preço de compra** (em USD):"
    )
    
    PROMPT_TOTAL_INVESTED = (
        "📊 **{symbol}** - Passo 2/2\n\n"
        "💵 **Preço de Compra:** ${price:,.6f}\n\n"
        "Digite o **valor total investido** (em USD):"
    )
    
    PROMPT_SELL_QUANTITY = (
        "📤 **Registrar Venda - {symbol}**\n\n"
        "📦 Quantidade disponível: {quantity:,.6f}\n\n"
        "Digite a **quantidade** que você vendeu:"
    )
    
    PROMPT_ENTRY_QUANTITY = (
        "➕ **Nova Entrada - {symbol}**\n\n"
        "Digite a **quantidade** comprada:"
    )
    
    PROMPT_RESERVE_TARGET = (
        "💵 **Configurar Meta de Reserva**\n\n"
        "Digite a porcentagem desejada para sua reserva em stablecoins:\n\n"
        "Exemplo: `15` para 15%\n\n"
        "💡 Recomendação: manter entre 10% e 20% do portfólio em stablecoins."
    )
    
    # ==========================================================================
    # FUTURES MESSAGES
    # ==========================================================================
    
    FUTURES_NEW_TRADE_PAIR = (
        "📝 **Nova Operação Futuros**\n\n"
        "📋 **Etapa 1/8 - Par de negociação**\n\n"
        "Digite o **par** da operação:\n\n"
        "Exemplos: `BTC/USDT`, `ETH/USDT`, `SOL`, `DOGE`\n"
        "Formatos especiais: `BTC.P`, `USDT.P`, `TOTAL`\n\n"
        "💡 Use `/` entre os pares. Se digitar apenas o símbolo (ex: `BTC`), será usado USDT como quote."
    )
    
    # ==========================================================================
    # CONFIRMATION MESSAGES
    # ==========================================================================
    
    CONFIRM_DELETE_ASSET = (
        "⚠️ **Remover {symbol}?**\n\n"
        "Esta ação não pode ser desfeita.\n"
        "Todas as entradas e histórico serão removidos."
    )
    
    # ==========================================================================
    # EMPTY STATE MESSAGES
    # ==========================================================================
    
    NO_ASSETS = "📊 Você não possui ativos cadastrados."
    NO_ENTRIES = "📋 **Entradas - {symbol}**\n\nNenhuma entrada registrada."
    NO_ALERTS = (
        "🔔 **Seus Alertas**\n\n"
        "Você não possui alertas recentes.\n\n"
        "Alertas são enviados automaticamente quando:\n"
        "• 🔴 Ativo cai 30%+ (oportunidade de preço médio)\n"
        "• 🟢 Ativo sobe 100%+ (sugestão de venda)\n"
        "• ☠️ Cruzamento da Morte detectado (sinal de baixa)"
    )
    
    NO_DEATH_CROSS = (
        "☠️ **Busca Cruzamento da Morte**\n\n"
        "✅ Nenhum dos seus ativos está em Cruzamento da Morte!\n\n"
        "Cruzamento da Morte ocorre quando a MA50 cruza abaixo da MA200,\n"
        "indicando possível tendência de baixa."
    )
    
    NO_GOLDEN_CROSS = (
        "✨ **Busca Cruzamento Dourado**\n\n"
        "Nenhum dos seus ativos está em Cruzamento Dourado no momento.\n\n"
        "Cruzamento Dourado ocorre quando a MA50 cruza acima da MA200,\n"
        "indicando possível tendência de alta."
    )
    
    NO_HIGH_RISK = (
        "⚠️ **Ativos em Risco**\n\n"
        "✅ Nenhum dos seus ativos está em situação de alto risco!\n\n"
        "Ativos são considerados de alto risco quando:\n"
        "• Possuem Cruzamento da Morte ativo\n"
        "• Queda de 30% ou mais do preço médio"
    )


# Create a singleton instance for easy import
MSG = Messages()


# Export both the class and instance
__all__ = ["Messages", "MSG"]
