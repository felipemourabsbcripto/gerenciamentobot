"""
Message formatters for the bot.
"""
from datetime import datetime
from typing import List, Optional
from src.models import Asset, Alert, FuturesTrade


def parse_us_number(value: str) -> float:
    """
    Parse number in any format - very flexible.
    Examples: 
        95,699.90 -> 95699.90 
        1,234,567.89 -> 1234567.89
        95.699,90 -> 95699.90 (Brazilian)
        0.00000001 -> 0.00000001
        $999,999.00 -> 999999.00
        1 -> 1.0
    """
    # Remove símbolos comuns
    value = value.strip()
    value = value.replace('$', '').replace('U$', '').replace('R$', '')
    value = value.replace(' ', '').replace('\t', '')
    
    # Se estiver vazio, retorna 0
    if not value:
        return 0.0
    
    # Detectar formato brasileiro (ponto como separador de milhares)
    if ',' in value and '.' in value:
        # Se vírgula vem depois do ponto, é formato US (1,234.56)
        if value.rfind('.') > value.rfind(','):
            value = value.replace(',', '')
        else:
            # Formato BR (1.234,56) -> converter para US
            value = value.replace('.', '').replace(',', '.')
    elif ',' in value and '.' not in value:
        # Pode ser formato BR (1234,56) ou US (1,234)
        parts = value.split(',')
        if len(parts) == 2 and len(parts[1]) <= 2:
            # Provavelmente BR: 1234,56 -> 1234.56
            value = value.replace(',', '.')
        else:
            # Formato US com separador de milhares: 1,234,567
            value = value.replace(',', '')
    
    return float(value)


def format_us_price(value: float) -> str:
    """
    Format price in US format (comma for thousands, dot for decimals).
    No limits on decimal places - shows all significant digits.
    Examples:
        99000 -> 99,000.00
        1234567.89 -> 1,234,567.89
        0.15 -> 0.15
        0.00015 -> 0.00015
        0.00000001 -> 0.00000001
        0.000000000001 -> 0.000000000001
    """
    if value is None or value == 0:
        return "0.00"
    
    abs_value = abs(value)
    
    # For values >= 1, use 2 decimal places
    if abs_value >= 1:
        return f"{value:,.2f}"
    
    # For small values, show all significant decimals
    # Convert to string to find significant digits
    str_val = f"{value:.12f}".rstrip('0')
    
    # Count decimal places needed
    if '.' in str_val:
        decimal_part = str_val.split('.')[1]
        decimal_places = len(decimal_part)
        # Minimum 2 decimal places
        decimal_places = max(2, decimal_places)
        return f"{value:,.{decimal_places}f}"
    
    return f"{value:,.2f}"


def format_price(value: float) -> str:
    """Format price intelligently based on value magnitude."""
    if value is None or value == 0:
        return "$0.00"
    
    abs_value = abs(value)
    
    if abs_value >= 1000:
        return f"${value:,.2f}"
    elif abs_value >= 1:
        return f"${value:,.2f}"
    elif abs_value >= 0.01:
        return f"${value:,.4f}"
    elif abs_value >= 0.0001:
        return f"${value:,.6f}"
    else:
        return f"${value:,.8f}"


def format_quantity(value: float, symbol: str = "") -> str:
    """Format quantity, removing trailing zeros."""
    if value is None or value == 0:
        return "0"
    
    # Format with up to 8 decimal places, then strip trailing zeros
    formatted = f"{value:,.8f}".rstrip('0').rstrip('.')
    
    if symbol:
        return f"{formatted} {symbol}"
    return formatted


def format_percent(value: float, with_sign: bool = True) -> str:
    """Format percentage value."""
    if value is None:
        return "0.00%"
    
    if with_sign:
        return f"{value:+.2f}%"
    return f"{value:.2f}%"


def format_pnl(value: float) -> str:
    """Format P&L with color emoji and sign."""
    if value is None:
        return "🔹 $0.00"
    
    emoji = "🟢" if value >= 0 else "🔴"
    return f"{emoji} ${value:+,.2f}"


class MessageFormatter:
    """Format messages for Telegram bot."""

    @staticmethod
    def welcome_message(first_name: str = "usuário") -> str:
        """Format welcome message."""
        return (
            f"🪙 **Gorni Capital**\n\n"
            f"**Gerenciador de Risco Exclusivo**\n\n"
            f"📊 Acompanha os ativos cadastrados\n"
            f"📈 Futuros & gerenciamento de risco\n"
            f"🛡️ Sugestões de segurança\n"
            f"🔔 **Receba alertas quando:**\n"
            f"   • Alerta para oportunidade de preço médio\n"
            f"   • Lucro no bolso: recomendação de venda parcial\n"
            f"   • Troca de ativo: sinal de forte tendência baixa\n"
            f"💵 Caixa de Oportunidades USDT – Meta 15%\n"
            f"📉 Análise Técnica Profissional\n"
            f"♟️ Estratégias Exclusivas Gorni Capital\n\n"
            f"Use o menu abaixo para navegar:"
        )

    @staticmethod
    def help_message() -> str:
        """Format help message."""
        return (
            "❓ **AJUDA - Crypto Portfolio Bot**\n\n"
            "**📊 Minha Carteira**\n"
            "Visualize todos os seus ativos cadastrados com preços atualizados.\n\n"
            "**➕ Adicionar Ativo**\n"
            "Adicione um novo ativo à sua carteira informando:\n"
            "• Moeda (busca por nome ou símbolo)\n"
            "• Quantidade comprada\n"
            "• Preço de compra\n\n"
            "**🔍 Buscar Moeda**\n"
            "Pesquise informações sobre qualquer criptomoeda.\n\n"
            "**📈 Top Moedas**\n"
            "Veja as 10 principais criptomoedas por capitalização.\n\n"
            "**💵 Reserva USDT**\n"
            "Gerencie sua reserva em USDT (meta de 15%).\n\n"
            "**📉 Análise Técnica**\n"
            "Detecte Death Cross e Golden Cross nos ativos.\n\n"
            "**⚙️ Configurações**\n"
            "• Ative/desative notificações\n"
            "• Configure alertas de Death Cross\n"
            "• Defina meta de reserva USDT\n\n"
            "**🔔 Alertas**\n"
            "O bot envia alertas automáticos quando:\n"
            "• 🔴 Ativo cai 30%+ → Oportunidade de preço médio\n"
            "• 🟢 Ativo sobe 100%+ → Recomendação de venda de 50%\n"
            "• ☠️ Death Cross detectado → Sinal de venda\n\n"
            "**Comandos disponíveis:**\n"
            "/start - Iniciar o bot\n"
            "/menu - Abrir menu principal\n"
            "/portfolio - Ver carteira\n"
            "/help - Esta ajuda"
        )

    @staticmethod
    def portfolio_summary(assets: List[Asset]) -> str:
        """Format portfolio summary."""
        if not assets:
            return (
                "📊 **Sua Carteira**\n\n"
                "🚫 Você ainda não possui ativos cadastrados.\n\n"
                "Use o botão **➕ Adicionar Ativo** para começar!"
            )

        # Filter confirmed assets only
        confirmed_assets = [a for a in assets if a.is_confirmed]
        
        if not confirmed_assets:
            return (
                "📊 **Sua Carteira**\n\n"
                "🚫 Você ainda não possui ativos confirmados.\n\n"
                "Use o botão **➕ Adicionar Ativo** para começar!"
            )

        total_invested = sum(a.quantity * (a.average_price or a.purchase_price) for a in confirmed_assets)
        total_current = sum((a.current_price or 0) * a.quantity for a in confirmed_assets)
        total_profit = total_current - total_invested
        profit_percent = (total_profit / total_invested * 100) if total_invested > 0 else 0

        emoji = "🟢" if total_profit >= 0 else "🔴"
        
        # Count risks
        death_cross_count = sum(1 for a in confirmed_assets if a.has_death_cross)
        big_loss_count = sum(1 for a in confirmed_assets 
                            if a.current_price and a.average_price 
                            and ((a.current_price - a.average_price) / a.average_price * 100) <= -30)
        
        lines = [
            "📊 **MINHA CARTEIRA**\n",
            "━━━━━━━━━━━━━━━━━━",
            f"💰 Investido: {format_price(total_invested)}",
            f"💎 Atual: {format_price(total_current)}",
            f"{emoji} P&L: {format_pnl(total_profit)} ({format_percent(profit_percent)})",
            "━━━━━━━━━━━━━━━━━━\n",
        ]
        
        # Risk warnings at top if any
        if death_cross_count > 0 or big_loss_count > 0:
            warnings = []
            if death_cross_count > 0:
                warnings.append(f"☠️ {death_cross_count} Death Cross")
            if big_loss_count > 0:
                warnings.append(f"📉 {big_loss_count} queda >30%")
            lines.insert(2, f"⚠️ **Alertas:** {' | '.join(warnings)}\n")
        
        lines.append("**📋 Ativos:**")
        
        for asset in confirmed_assets:
            current_value = (asset.current_price or 0) * asset.quantity
            avg_price = asset.average_price or asset.purchase_price
            profit_pct = ((asset.current_price or avg_price) - avg_price) / avg_price * 100 if avg_price > 0 else 0
            
            # Choose emoji based on status
            if asset.has_death_cross:
                asset_emoji = "☠️"
            elif profit_pct >= 0:
                asset_emoji = "🟢"
            else:
                asset_emoji = "🔴"
            
            # Compact single-line format
            lines.append(
                f"{asset_emoji} **{asset.symbol.upper()}** | "
                f"{format_quantity(asset.quantity)} | "
                f"{format_price(current_value)} | "
                f"{format_percent(profit_pct)}"
            )

        return "\n".join(lines)

    @staticmethod
    def asset_detail(asset: Asset) -> str:
        """Format detailed asset information."""
        current_price = asset.current_price or asset.purchase_price
        avg_price = asset.average_price or asset.purchase_price
        current_value = current_price * asset.quantity
        total_invested = avg_price * asset.quantity
        profit = current_value - total_invested
        profit_pct = ((current_price - avg_price) / avg_price) * 100 if avg_price > 0 else 0
        
        emoji = "🟢" if profit >= 0 else "🔴"
        
        # Risk warnings
        warnings = []
        if asset.has_death_cross:
            warnings.append("☠️ **DEATH CROSS ATIVO**")
        if profit_pct <= -30:
            warnings.append("📉 **QUEDA SIGNIFICATIVA**")
        elif profit_pct >= 100:
            warnings.append("🚀 **CONSIDERE VENDA PARCIAL**")
        
        warning_section = "\n".join(warnings) + "\n\n" if warnings else ""
        
        # Calculate exposure if we had total portfolio (simplified)
        qty_display = format_quantity(asset.quantity, asset.symbol.upper())
        
        return (
            f"{warning_section}"
            f"📊 **{asset.name}** ({asset.symbol.upper()})\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"📈 **Preço Atual:** {format_price(current_price)}\n"
            f"💰 **Preço Médio:** {format_price(avg_price)}\n"
            f"{emoji} **Variação:** {format_percent(profit_pct)}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📦 **Quantidade:** {qty_display}\n"
            f"💵 **Investido:** {format_price(total_invested)}\n"
            f"💎 **Valor Atual:** {format_price(current_value)}\n"
            f"{format_pnl(profit)}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📅 Adicionado: {asset.created_at.strftime('%d/%m/%Y')}"
        )

    @staticmethod
    def alerts_list(alerts: List[Alert]) -> str:
        """Format alerts list."""
        if not alerts:
            return (
                "🔔 **Seus Alertas**\n\n"
                "✅ Você não tem alertas pendentes!"
            )

        lines = ["🔔 **Alertas Recentes:**\n"]
        
        for alert in alerts[:10]:
            emoji = "🔴" if alert.alert_type == "drop_30" else "🟢"
            status = "📬" if not alert.is_read else "📭"
            date = alert.created_at.strftime('%d/%m %H:%M')
            
            lines.append(f"{status} {emoji} [{date}] {alert.message[:50]}...")

        return "\n".join(lines)

    @staticmethod
    def coin_info(coin) -> str:
        """Format coin information."""
        if hasattr(coin, 'price_change_percentage_24h'):
            change = coin.price_change_percentage_24h
            price = coin.current_price
            name = coin.name
            symbol = coin.symbol
            market_cap = getattr(coin, 'market_cap', 0)
        else:
            change = coin.get('change_24h', 0)
            price = coin.get('price', 0)
            name = coin.get('name', 'Unknown')
            symbol = coin.get('symbol', '???')
            market_cap = coin.get('market_cap', 0)
            
        change_emoji = "🟢" if change >= 0 else "🔴"
        
        return (
            f"🪙 **{name}** ({symbol.upper()})\n\n"
            f"💰 **Preço Atual:** ${price:,.6f}\n"
            f"{change_emoji} **Variação 24h:** {change:+.2f}%\n"
            f"📊 **Market Cap:** ${market_cap:,.0f}\n"
        )

    @staticmethod
    def settings_info(user) -> str:
        """Format settings information."""
        notif_status = "🔔 Ativadas" if user.notifications_enabled else "🔕 Desativadas"
        dc_status = "🔔 Ativados" if user.death_cross_alerts else "🔕 Desativados"
        reserve_target = getattr(user, 'reserve_target_percent', 15) or 15
        
        return (
            "⚙️ **Configurações**\n\n"
            f"🔔 **Notificações:** {notif_status}\n"
            f"📉 **Alertas Death Cross:** {dc_status}\n"
            f"💵 **Meta de Reserva:** {reserve_target}%\n\n"
            "Selecione uma opção para configurar:"
        )

    # ==================== FUTURES MESSAGES ====================

    @staticmethod
    def futures_menu_message() -> str:
        """Format futures menu message."""
        return (
            "📈 **Menu de Futuros**\n\n"
            "Gerencie suas posições alavancadas em contratos futuros.\n\n"
            "⚠️ **AVISO DE RISCO:**\n"
            "• Alavancagem amplifica ganhos E perdas\n"
            "• Altcoins com >3x = Alto Risco de Liquidação\n"
            "• Use sempre Stop!\n\n"
            "Selecione uma opção:"
        )

    @staticmethod
    def futures_risk_warning(leverage: int, is_altcoin: bool, symbol: str) -> str:
        """Format risk warning for futures trade."""
        risk_level = "EXTREMO" if leverage >= 10 else "ALTO"
        
        lines = [
            f"⚠️ **AVISO DE {risk_level} RISCO** ⚠️\n",
        ]
        
        if is_altcoin and leverage > 3:
            lines.append(
                f"🔴 **{symbol}** é uma altcoin com **{leverage}x** de alavancagem!\n\n"
                f"**Riscos específicos de altcoins:**\n"
                f"• Maior volatilidade que BTC/ETH\n"
                f"• Menor liquidez = slippage maior\n"
                f"• Risco elevado de liquidação\n"
            )
        
        if leverage >= 10:
            # Cálculo mais preciso considerando MMR de 0.5%
            # Margem sustentável = 100% - 0.5% = 99.5% → divido por alavancagem
            liq_percent = round((100 - 0.5) / leverage, 1)
            lines.append(
                f"\n💀 **Com {leverage}x:**\n"
                f"• Liquidação em aprox. **~{liq_percent}%** de movimento contra\n"
                f"• Perdas podem superar o depósito inicial\n"
            )
        
        lines.append(
            "\n**Recomendações:**\n"
            f"• Use stop loss próximo ao entry\n"
            f"• Arrisque no máximo 1-2% do capital\n"
            f"• Considere reduzir alavancagem para <= 3x"
        )
        
        return "\n".join(lines)

    @staticmethod
    def futures_open_positions(trades: List, stats: dict) -> str:
        """Format open futures positions list."""
        if not trades:
            return (
                "📈 **Posições Abertas (Futuros)**\n\n"
                "🚫 Você não tem posições abertas.\n\n"
                "Use **➕ Nova Operação** para abrir uma posição!"
            )
        
        total_margin = stats.get('total_margin', 0)
        unrealized_pnl = stats.get('unrealized_pnl', 0)
        pnl_emoji = "🟢" if unrealized_pnl >= 0 else "🔴"
        
        lines = [
            "📈 **Posições Abertas (Futuros)**\n",
            f"💰 **Margem Total:** ${total_margin:,.2f}",
            f"{pnl_emoji} **P/L Não Realizado:** ${unrealized_pnl:+,.2f}\n",
            "━━━━━━━━━━━━━━━━━━━━\n"
        ]
        
        for trade in trades:
            side_emoji = "🟢 COMPRA" if trade.side == "long" else "🔴 VENDA"
            risk_emoji = "⚠️" if trade.risk_level in ["high", "extreme"] else ""
            pnl = trade.unrealized_pnl or 0
            pnl_pct = trade.unrealized_pnl_percent or 0
            trade_pnl_emoji = "🟢" if pnl >= 0 else "🔴"
            
            lines.append(
                f"{risk_emoji}{side_emoji} **{trade.pair}** @ {trade.leverage}x\n"
                f"   📥 Entrada: ${trade.entry_price:,.4f}\n"
                f"   📊 Atual: ${trade.current_price or trade.entry_price:,.4f}\n"
                f"   {trade_pnl_emoji} P/L: ${pnl:+,.2f} ({pnl_pct:+.2f}%)\n"
            )
        
        lines.append("\n*Clique em um trade para mais ações*")
        return "\n".join(lines)

    @staticmethod
    def futures_trade_detail(trade) -> str:
        """Format detailed futures trade information."""
        side_emoji = "🟢 COMPRA" if trade.side == "long" else "🔴 VENDA"
        
        # Risk indicator
        risk_emoji = ""
        risk_text = ""
        if trade.risk_level == "extreme":
            risk_emoji = "💀"
            risk_text = "RISCO EXTREMO"
        elif trade.risk_level == "high":
            risk_emoji = "⚠️"
            risk_text = "ALTO RISCO"
        
        risk_line = f"\n{risk_emoji} **{risk_text}**\n" if risk_text else ""
        
        # Calculate values
        pnl = trade.unrealized_pnl or 0
        pnl_pct = trade.unrealized_pnl_percent or 0
        entry = trade.entry_price
        current = trade.current_price or entry
        liq_price = trade.liquidation_price
        
        lines = [
            f"📊 **{trade.pair}** {side_emoji} {trade.leverage}x{risk_line}",
            f"━━━━━━━━━━━━━━━━━━",
            f"📥 Entrada: {format_price(entry)}",
            f"📈 Atual: {format_price(current)}",
            f"📦 Qtd: {format_quantity(trade.quantity)}",
            f"💰 Margem: {format_price(trade.margin)}",
            f"━━━━━━━━━━━━━━━━━━",
            f"{format_pnl(pnl)} ({format_percent(pnl_pct)})",
        ]
        
        if liq_price:
            # Distance to liquidation
            if trade.side == "long":
                liq_distance = ((current - liq_price) / current) * 100
            else:
                liq_distance = ((liq_price - current) / current) * 100
            lines.append(f"💀 Liquidação: {format_price(liq_price)} ({liq_distance:.1f}% away)")
        
        # R:R Ratio calculation
        sl_line = ""
        tp_line = ""
        rr_line = ""
        
        if trade.stop_loss:
            if trade.side == "long":
                sl_pct = ((entry - trade.stop_loss) / entry) * 100
            else:
                sl_pct = ((trade.stop_loss - entry) / entry) * 100
            sl_line = f"🛑 Stop: {format_price(trade.stop_loss)} (-{sl_pct:.2f}%)"
            lines.append(sl_line)
        
        if trade.take_profit:
            if trade.side == "long":
                tp_pct = ((trade.take_profit - entry) / entry) * 100
            else:
                tp_pct = ((entry - trade.take_profit) / entry) * 100
            tp_line = f"🎯 Alvo: {format_price(trade.take_profit)} (+{tp_pct:.2f}%)"
            lines.append(tp_line)
        
        # Calculate Risk:Reward ratio if both SL and TP are set
        if trade.stop_loss and trade.take_profit:
            if trade.side == "long":
                risk = entry - trade.stop_loss
                reward = trade.take_profit - entry
            else:
                risk = trade.stop_loss - entry
                reward = entry - trade.take_profit
            
            if risk > 0 and reward > 0:
                rr_ratio = reward / risk
                rr_emoji = "✅" if rr_ratio >= 2 else "⚠️" if rr_ratio >= 1 else "❌"
                lines.append(f"{rr_emoji} **R:R Ratio:** 1:{rr_ratio:.2f}")
        
        lines.append(f"━━━━━━━━━━━━━━━━━━")
        lines.append(f"📅 Aberto: {trade.opened_at.strftime('%d/%m/%Y %H:%M')}")
        
        if trade.notes:
            lines.append(f"📝 {trade.notes}")
        
        return "\n".join(lines)

    @staticmethod
    def futures_new_trade_summary(
        pair: str,
        side: str,
        leverage: int,
        entry_price: float,
        quantity: float,
        margin: float,
        is_altcoin: bool,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> str:
        """Format new trade confirmation summary."""
        side_emoji = "🟢 COMPRA" if side == "long" else "🔴 VENDA"
        
        # Calculate risk
        risk_level = "normal"
        risk_warning = ""
        if leverage >= 10:
            risk_level = "extreme"
            risk_warning = "\n💀 **RISCO EXTREMO** - Liquidação em ~9% de movimento!\n"
        elif leverage > 3 and is_altcoin:
            risk_level = "high"
            risk_warning = "\n⚠️ **ALTO RISCO** - Altcoin com alta alavancagem!\n"
        elif leverage > 5:
            risk_level = "high"
            risk_warning = "\n⚠️ **ALTO RISCO** - Alavancagem elevada!\n"
        
        position_value = quantity * entry_price
        leveraged_value = position_value * leverage
        
        lines = [
            "📝 **Confirmar Nova Operação**\n",
            risk_warning,
            f"🪙 **Par:** {pair}",
            f"📍 **Lado:** {side_emoji}",
            f"⚡ **Alavancagem:** {leverage}x",
            f"━━━━━━━━━━━━━━━━━━━━",
            f"📥 **Preço Entrada:** ${entry_price:,.6f}",
            f"📦 **Quantidade:** {quantity:,.6f}",
            f"💰 **Margem:** ${margin:,.2f}",
            f"📊 **Valor da Posição:** ${leveraged_value:,.2f}",
        ]
        
        if stop_loss:
            lines.append(f"🛑 **Stop:** ${stop_loss:,.6f}")
        
        if take_profit:
            lines.append(f"🎯 **Alvo:** ${take_profit:,.6f}")
        
        return "\n".join(lines)

    @staticmethod
    def futures_history_message(trades: List, stats: dict) -> str:
        """Format futures trade history."""
        if not trades:
            return (
                "📊 **Histórico de Operações**\n\n"
                "🚫 Você não tem trades finalizados.\n"
            )
        
        realized_pnl = stats.get('realized_pnl', 0)
        win_rate = stats.get('win_rate', 0)
        pnl_emoji = "🟢" if realized_pnl >= 0 else "🔴"
        
        lines = [
            "📊 **Histórico de Operações**\n",
            f"📈 **Taxa de Acerto:** {win_rate:.1f}%",
            f"{pnl_emoji} **P/L Total Realizado:** ${realized_pnl:+,.2f}\n",
            "━━━━━━━━━━━━━━━━━━━━\n"
        ]
        
        for trade in trades[:10]:
            pnl = trade.pnl or 0
            pnl_emoji = "🟢" if pnl >= 0 else "🔴"
            date = trade.closed_at.strftime('%d/%m') if trade.closed_at else "N/A"
            status = "✅" if trade.status == "closed" else "💀"
            
            lines.append(
                f"{pnl_emoji} {status} **{trade.pair}** {trade.leverage}x\n"
                f"   💵 P/L: ${pnl:+,.2f} | 📅 {date}\n"
            )
        
        return "\n".join(lines)

    @staticmethod
    def futures_stats_message(stats: dict) -> str:
        """Format futures trading statistics."""
        open_count = stats.get('open_count', 0)
        closed_count = stats.get('closed_count', 0)
        total_margin = stats.get('total_margin', 0)
        unrealized = stats.get('unrealized_pnl', 0)
        realized = stats.get('realized_pnl', 0)
        win_rate = stats.get('win_rate', 0)
        winning = stats.get('winning_trades', 0)
        losing = stats.get('losing_trades', 0)
        
        unrealized_emoji = "🟢" if unrealized >= 0 else "🔴"
        realized_emoji = "🟢" if realized >= 0 else "🔴"
        
        return (
            "📉 **Estatísticas de Futuros**\n\n"
            f"📈 **Posições Abertas:** {open_count}\n"
            f"💰 **Margem em Uso:** ${total_margin:,.2f}\n"
            f"{unrealized_emoji} **P/L Não Realizado:** ${unrealized:+,.2f}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 **Operações Encerradas:** {closed_count}\n"
            f"✅ **Operações Ganhas:** {winning}\n"
            f"❌ **Operações Perdidas:** {losing}\n"
            f"📈 **Taxa de Acerto:** {win_rate:.1f}%\n"
            f"{realized_emoji} **P/L Total Realizado:** ${realized:+,.2f}"
        )

    @staticmethod
    def futures_high_risk_warning(trades: List) -> str:
        """Format high risk trades warning message."""
        if not trades:
            return (
                "⚠️ **Operações de Alto Risco**\n\n"
                "✅ Você não tem trades de alto risco abertos.\n\n"
                "**Lembrete:** Evite alavancagem >3x em altcoins!"
            )
        
        lines = [
            "⚠️ **TRADES DE ALTO RISCO**\n",
            "Os seguintes trades requerem atenção:\n"
        ]
        
        for trade in trades:
            risk_emoji = "💀" if trade.risk_level == "extreme" else "⚠️"
            reason = ""
            if trade.is_altcoin and trade.leverage > 3:
                reason = f"Altcoin com {trade.leverage}x"
            elif trade.leverage >= 10:
                reason = f"Alavancagem extrema ({trade.leverage}x)"
            else:
                reason = f"Alavancagem alta ({trade.leverage}x)"
            
            lines.append(
                f"{risk_emoji} **{trade.pair}** - {reason}\n"
            )
        
        lines.append(
            "\n**Recomendações:**\n"
            "• Considere reduzir a posição\n"
            "• Ajuste o Stop\n"
            "• Monitore de perto"
        )
        
        return "\n".join(lines)

    @staticmethod
    def futures_closed_trade_summary(trade) -> str:
        """Format closed trade summary."""
        side_emoji = "🟢 COMPRA" if trade.side == "long" else "🔴 VENDA"
        pnl = trade.pnl or 0
        pnl_pct = trade.pnl_percent or 0
        pnl_emoji = "🟢" if pnl >= 0 else "🔴"
        
        status_text = "Fechado ✅" if trade.status == "closed" else "Liquidado 💀"
        
        return (
            f"📊 **Operação {status_text}**\n\n"
            f"🪙 **Par:** {trade.pair}\n"
            f"📍 **Lado:** {side_emoji}\n"
            f"⚡ **Alavancagem:** {trade.leverage}x\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📥 **Entry:** ${trade.entry_price:,.6f}\n"
            f"📤 **Saída:** ${trade.current_price:,.6f}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{pnl_emoji} **P/L Final:** ${pnl:+,.2f} ({pnl_pct:+.2f}%)\n"
            f"📅 **Fechado em:** {trade.closed_at.strftime('%d/%m/%Y %H:%M') if trade.closed_at else 'N/A'}"
        )

    @staticmethod
    def futures_full_trade_summary(trade_data: dict, current_price: float = None) -> str:
        """
        Format complete futures trade summary with all registration steps visible.
        
        Follows the format:
        - Par selecionado
        - Preço de compra
        - Valor investido
        - Long/Short
        - Alavancagem
        - Stop Loss
        - Alvos de venda
        - Timeframe
        - Cálculo de risco
        """
        now = datetime.now()
        pair = trade_data.get('pair', '???')
        entry_price = trade_data.get('entry_price', 0)
        side = trade_data.get('side', 'long')
        leverage = trade_data.get('leverage', 1)
        stop_loss = trade_data.get('stop_loss', 0)
        stop_percent = trade_data.get('stop_percent', 0)
        margin = trade_data.get('margin', 0)
        quantity = trade_data.get('quantity', 0)
        timeframe = trade_data.get('timeframe', '4h')
        futures_balance = trade_data.get('futures_balance', 0)
        risk_percent = trade_data.get('risk_percent', 5.0)
        risk_usd = trade_data.get('risk_usd', 0)
        open_risk = trade_data.get('open_risk', 0)
        
        # Targets
        target_1 = trade_data.get('target_1', {})
        target_2 = trade_data.get('target_2', {})
        target_3 = trade_data.get('target_3', {})
        
        # Calculate values
        position_value = margin * leverage
        allocation_percent = (margin / futures_balance * 100) if futures_balance > 0 else 0
        max_risk = futures_balance * (risk_percent / 100)
        available_risk = max_risk - open_risk - risk_usd
        
        side_emoji = "🟢 COMPRA" if side == "long" else "🔴 VENDA"
        side_text = "LONG" if side == "long" else "SHORT"
        
        # Current price
        price_display = current_price if current_price else entry_price
        
        # Leverage warning
        lev_warning = ""
        if leverage >= 20:
            lev_warning = "💀 RISCO EXTREMO"
        elif leverage >= 10:
            lev_warning = "⚠️ Risco Alto"
        elif leverage >= 5:
            lev_warning = "⚠️ Atenção à volatilidade"
        
        lines = [
            f"📋 **RESUMO DO TRADE**\n",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
            f"📝 **1. Par selecionado:** {pair}",
            f"💵 **2. Preço de compra:** U$ {format_us_price(entry_price)}",
            f"💰 **3. Valor investido:** U$ {format_us_price(margin)} ({allocation_percent:.2f}% da carteira)",
            f"{side_emoji} **4. Direção:** {side_text}",
            f"⚡ **5. Alavancagem:** {leverage}x {lev_warning}",
            f"🛑 **6. Stop Loss:** U$ {format_us_price(stop_loss)} ({stop_percent:.2f}%)",
        ]
        
        # Targets
        lines.append(f"\n🎯 **7. Alvos de Venda:**")
        if target_1:
            t1_profit = ((target_1.get('price', 0) - entry_price) / entry_price * 100) if entry_price > 0 else 0
            if side == 'short':
                t1_profit = -t1_profit
            lines.append(f"   🔜 1º Alvo: U$ {format_us_price(target_1.get('price', 0))} > {target_1.get('percent', 0):.0f}% (Lucro {t1_profit:.1f}%)")
        if target_2:
            t2_profit = ((target_2.get('price', 0) - entry_price) / entry_price * 100) if entry_price > 0 else 0
            if side == 'short':
                t2_profit = -t2_profit
            lines.append(f"   🔜 2º Alvo: U$ {format_us_price(target_2.get('price', 0))} > {target_2.get('percent', 0):.0f}% (Lucro {t2_profit:.1f}%)")
        if target_3:
            t3_profit = ((target_3.get('price', 0) - entry_price) / entry_price * 100) if entry_price > 0 else 0
            if side == 'short':
                t3_profit = -t3_profit
            lines.append(f"   🔜 3º Alvo: U$ {format_us_price(target_3.get('price', 0))} > {target_3.get('percent', 0):.0f}% (Lucro {t3_profit:.1f}%)")
        
        lines.append(f"\n📊 **8. Timeframe:** {timeframe.upper()}")
        
        lines.append(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"\n� **DETALHES DA POSIÇÃO (Margem/Colateral):**")
        lines.append(f"   💰 **Margem:** U$ {format_us_price(margin)}")
        lines.append(f"   📊 **Posição Total:** U$ {format_us_price(position_value)} ({leverage}x)")
        lines.append(f"   📦 **Quantidade:** {quantity:,.6f} contratos")
        lines.append(f"   📈 **Alocação:** {allocation_percent:.2f}% da carteira")
        
        lines.append(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"\n💲 **Preço atual:** U$ {format_us_price(price_display)}")
        lines.append(f"⌚ **Atualizado em:** {now.strftime('%d/%m/%Y às %H:%M:%S')}")
        
        lines.append(f"\n➡️ **Preço de compra:** U$ {format_us_price(entry_price)}")
        lines.append(f"➡️ **Valor Investido:** U$ {format_us_price(margin)}")
        lines.append(f"➡️ **Posição Alavancada:** U$ {format_us_price(position_value)}")
        lines.append(f"➡️ **Alavancagem:** {leverage}x")
        
        lines.append(f"\n🎯 **Bons alvos de venda:**")
        if target_1:
            t1_profit = ((target_1.get('price', 0) - entry_price) / entry_price * 100 * leverage) if entry_price > 0 else 0
            if side == 'short':
                t1_profit = -t1_profit
            lines.append(f"🔜 1ª Zona de venda: U$ {format_us_price(target_1.get('price', 0))} - Vender {target_1.get('percent', 0):.0f}% (Lucro {t1_profit:.1f}%)")
        if target_2:
            t2_profit = ((target_2.get('price', 0) - entry_price) / entry_price * 100 * leverage) if entry_price > 0 else 0
            if side == 'short':
                t2_profit = -t2_profit
            lines.append(f"🔜 2ª Zona de venda: U$ {format_us_price(target_2.get('price', 0))} - Vender {target_2.get('percent', 0):.0f}% (Lucro {t2_profit:.1f}%)")
        if target_3:
            t3_profit = ((target_3.get('price', 0) - entry_price) / entry_price * 100 * leverage) if entry_price > 0 else 0
            if side == 'short':
                t3_profit = -t3_profit
            lines.append(f"🔜 3ª Zona de venda: U$ {format_us_price(target_3.get('price', 0))} - Vender {target_3.get('percent', 0):.0f}% (Lucro {t3_profit:.1f}%)")
        
        lines.append(f"\n🛑️ **Stoploss:** U$ {format_us_price(stop_loss)} (-{stop_percent:.2f}%)")
        lines.append(f"💰 **Carteira de Futuros:** U$ {format_us_price(futures_balance)}")
        lines.append(f"⚙️ **Risco configurado:** {risk_percent:.1f}% da carteira de futuros")
        lines.append(f"💵 **Risco máximo:** U$ {format_us_price(max_risk)}")
        lines.append(f"🔒 **Risco em uso:** U$ {format_us_price(open_risk + risk_usd)}")
        lines.append(f"✅ **Risco Disponível:** U$ {format_us_price(available_risk)}")
        
        return "\n".join(lines)

    @staticmethod
    def futures_registration_step(step: int, trade_data: dict) -> str:
        """Format current registration step with all previous steps visible."""
        pair = trade_data.get('pair', '???')
        entry_price = trade_data.get('entry_price', 0)
        side = trade_data.get('side', '')
        leverage = trade_data.get('leverage', 0)
        stop_loss = trade_data.get('stop_loss', 0)
        stop_percent = trade_data.get('stop_percent', 0)
        margin = trade_data.get('margin', 0)
        current_price = trade_data.get('current_price', 0)
        futures_balance = trade_data.get('futures_balance', 0)
        
        side_emoji = "🟢 COMPRA" if side == "long" else "🔴 VENDA" if side else "❓"
        
        lines = [
            f"📋 **CADASTRO DE TRADE FUTUROS**\n",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
        ]
        
        # Show completed steps
        if pair:
            lines.append(f"✅ 1. Par: **{pair}**")
        else:
            lines.append(f"⏳ 1. Par: _aguardando..._")
        
        if entry_price > 0:
            lines.append(f"✅ 2. Entrada: **U$ {format_us_price(entry_price)}**")
        elif step >= 2:
            lines.append(f"⏳ 2. Entrada: _aguardando..._")
        
        if side:
            lines.append(f"✅ 3. Direção: **{side_emoji}**")
        elif step >= 3:
            lines.append(f"⏳ 3. Direção: _aguardando..._")
        
        if leverage > 0:
            lines.append(f"✅ 4. Alavancagem: **{leverage}x**")
        elif step >= 4:
            lines.append(f"⏳ 4. Alavancagem: _aguardando..._")
        
        if stop_loss > 0:
            lines.append(f"✅ 5. Stop Loss: **U$ {format_us_price(stop_loss)}** ({stop_percent:.2f}%)")
        elif step >= 5:
            lines.append(f"⏳ 5. Stop Loss: _aguardando..._")
        
        if step >= 6:
            targets = trade_data.get('targets', [])
            if targets:
                lines.append(f"✅ 6. Alvos de venda: **{len(targets)} alvos**")
            else:
                lines.append(f"⏳ 6. Alvos de venda: _aguardando..._")
        
        if step >= 7:
            timeframe = trade_data.get('timeframe', '')
            if timeframe:
                lines.append(f"✅ 8. Timeframe: **{timeframe.upper()}**")
            else:
                lines.append(f"⏳ 8. Timeframe: _aguardando..._")
        
        if step >= 8:
            lines.append(f"⏳ 8. Cálculo de risco: _processando..._")
        
        # Show current price
        if current_price > 0:
            lines.append(f"\n💰 **Preço atual:** U$ {format_us_price(current_price)}")
        
        # Show balance info
        if futures_balance > 0:
            lines.append(f"💼 **Carteira Futuros:** U$ {format_us_price(futures_balance)}")
        
        return "\n".join(lines)
