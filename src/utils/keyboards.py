"""
Keyboard utilities for Telegram inline keyboards.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Optional


class KeyboardBuilder:
    """Builder class for creating Telegram inline keyboards."""

    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Create main menu keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("📊 Gorni Carteira", callback_data="portfolio"),
                InlineKeyboardButton("📈 Gorni Futuros", callback_data="futures_menu"),
            ],
            [
                InlineKeyboardButton("🧠 Gorni Estratégias", callback_data="gg_menu"),
            ],
            [
                InlineKeyboardButton("⚠️ Gorni Risco", callback_data="risk_panel"),
            ],
            [
                InlineKeyboardButton("➕ Adicionar Ativo", callback_data="add_asset"),
                InlineKeyboardButton("🔎 Analisar Ativo", callback_data="analyze_asset"),
            ],
            [
                InlineKeyboardButton("🔔 Alertas Gorni", callback_data="whale_alert"),
                InlineKeyboardButton("💵 Gorni Reserva", callback_data="reserve_status"),
            ],
            [
                InlineKeyboardButton("📉 Gorni Análise", callback_data="technical_menu"),
                InlineKeyboardButton("⚙️ Configurações", callback_data="settings"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_to_menu() -> InlineKeyboardMarkup:
        """Create back to menu keyboard."""
        keyboard = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")]]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def settings_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
        """Create settings menu keyboard."""
        keyboard = [
            [InlineKeyboardButton("📋 Meus Dados", callback_data="my_profile_data")],
            [InlineKeyboardButton("🔔 Notificações On/Off", callback_data="toggle_notifications")],
            [InlineKeyboardButton("📊 Alertas Death Cross On/Off", callback_data="toggle_death_cross")],
            [InlineKeyboardButton("📈 Alertas de Preço On/Off", callback_data="toggle_price_alerts")],
            [InlineKeyboardButton("⏱️ Intervalo de Verificação", callback_data="set_check_interval")],
            [InlineKeyboardButton("💵 Configurar Meta Reserva", callback_data="set_reserve_target")],
            [InlineKeyboardButton("💰 Atualizar Saldo Futuros", callback_data="update_futures_balance")],
            [InlineKeyboardButton("⚙️ Risco por Trade (%)", callback_data="set_futures_risk_percent")],
        ]
        if is_admin:
            keyboard.append([InlineKeyboardButton("🔐 Painel Admin", callback_data="admin_panel")])
        keyboard.append([InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def check_interval_menu() -> InlineKeyboardMarkup:
        """Create check interval selection keyboard."""
        keyboard = [
            [InlineKeyboardButton("⚡ 5 minutos", callback_data="interval_5")],
            [InlineKeyboardButton("🕐 10 minutos", callback_data="interval_10")],
            [InlineKeyboardButton("🕑 30 minutos", callback_data="interval_30")],
            [InlineKeyboardButton("🕐 1 hora", callback_data="interval_60")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="settings")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def analyze_asset_timeframe() -> InlineKeyboardMarkup:
        """Create timeframe selection keyboard for asset analysis."""
        keyboard = [
            [
                InlineKeyboardButton("5m", callback_data="analyze_tf_5m"),
                InlineKeyboardButton("15m", callback_data="analyze_tf_15m"),
                InlineKeyboardButton("30m", callback_data="analyze_tf_30m"),
            ],
            [
                InlineKeyboardButton("1H", callback_data="analyze_tf_1h"),
                InlineKeyboardButton("4H", callback_data="analyze_tf_4h"),
                InlineKeyboardButton("1D", callback_data="analyze_tf_1d"),
            ],
            [
                InlineKeyboardButton("1W", callback_data="analyze_tf_1w"),
                InlineKeyboardButton("1M", callback_data="analyze_tf_1M"),
            ],
            [InlineKeyboardButton("❌ Cancelar", callback_data="menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def analyze_result_actions(symbol: str) -> InlineKeyboardMarkup:
        """Create actions keyboard after analysis result."""
        keyboard = [
            [InlineKeyboardButton("🔄 Analisar Outro Tempo", callback_data=f"analyze_change_tf_{symbol}")],
            [InlineKeyboardButton("📈 Abrir Trade Futuros", callback_data="futures_add")],
            [InlineKeyboardButton("➕ Adicionar à Carteira", callback_data="add_asset")],
            [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def portfolio_actions() -> InlineKeyboardMarkup:
        """Create portfolio actions keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("🔄 Atualizar Preços", callback_data="refresh_prices"),
                InlineKeyboardButton("➕ Adicionar Ativo", callback_data="add_asset"),
            ],
            [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def asset_actions(asset_id: int) -> InlineKeyboardMarkup:
        """Create asset actions keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("📊 Ver Detalhes", callback_data=f"asset_detail_{asset_id}"),
                InlineKeyboardButton("📈 Análise Técnica", callback_data=f"full_analysis_{asset_id}"),
            ],
            [
                InlineKeyboardButton("➕ Nova Entrada", callback_data=f"add_entry_{asset_id}"),
                InlineKeyboardButton("📋 Ver Entradas", callback_data=f"view_entries_{asset_id}"),
            ],
            [
                InlineKeyboardButton("📤 Registrar Venda", callback_data=f"asset_sell_{asset_id}"),
                InlineKeyboardButton("🗑️ Remover Ativo", callback_data=f"asset_delete_{asset_id}"),
            ],
            [InlineKeyboardButton("🔙 Voltar à Carteira", callback_data="portfolio")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def confirm_action(action: str, item_id: int) -> InlineKeyboardMarkup:
        """Create confirmation keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirmar", callback_data=f"confirm_{action}_{item_id}"),
                InlineKeyboardButton("❌ Cancelar", callback_data=f"cancel_{action}"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def coin_search_results(coins: List[dict]) -> InlineKeyboardMarkup:
        """Create keyboard for coin search results."""
        keyboard = []
        for coin in coins[:8]:
            keyboard.append([
                InlineKeyboardButton(
                    f"{coin['symbol'].upper()} - {coin['name'][:30]}",
                    callback_data=f"select_coin_{coin['id']}"
                )
            ])
        keyboard.append([InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def alert_response(alert_type: str, asset_id: int) -> InlineKeyboardMarkup:
        """Create keyboard for alert response actions."""
        if alert_type == "drop":
            keyboard = [
                [InlineKeyboardButton("➕ Fazer Preço Médio", callback_data=f"asset_average_{asset_id}")],
                [InlineKeyboardButton("📊 Ver Detalhes", callback_data=f"asset_detail_{asset_id}")],
                [InlineKeyboardButton("❌ Ignorar", callback_data="dismiss_alert")],
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("📤 Registrar Venda Parcial", callback_data=f"asset_sell_{asset_id}")],
                [InlineKeyboardButton("📊 Ver Detalhes", callback_data=f"asset_detail_{asset_id}")],
                [InlineKeyboardButton("❌ Ignorar", callback_data="dismiss_alert")],
            ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def alerts_list(has_alerts: bool) -> InlineKeyboardMarkup:
        """Create keyboard for alerts list."""
        keyboard = []
        if has_alerts:
            keyboard.append([InlineKeyboardButton("✅ Marcar Todos como Lidos", callback_data="mark_all_read")])
        keyboard.append([InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def top_coins_list(coins: List) -> InlineKeyboardMarkup:
        """Create keyboard for top coins list."""
        keyboard = []
        for i, coin in enumerate(coins[:10], 1):
            keyboard.append([
                InlineKeyboardButton(
                    f"{i}. {coin.symbol.upper()} - ${coin.current_price:,.2f}",
                    callback_data=f"coin_info_{coin.id}"
                )
            ])
        keyboard.append([InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def add_to_portfolio(coin_id: str) -> InlineKeyboardMarkup:
        """Create keyboard to add coin to portfolio."""
        keyboard = [
            [InlineKeyboardButton("➕ Adicionar à Carteira", callback_data=f"add_coin_{coin_id}")],
            [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def cancel_action() -> InlineKeyboardMarkup:
        """Create cancel keyboard."""
        keyboard = [[InlineKeyboardButton("❌ Cancelar", callback_data="cancel")]]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def yes_no(action: str, item_id: int = 0) -> InlineKeyboardMarkup:
        """Create yes/no keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("✅ Sim", callback_data=f"yes_{action}_{item_id}"),
                InlineKeyboardButton("❌ Não", callback_data=f"no_{action}"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def confirm_asset_add(symbol: str, name: str, price: float) -> InlineKeyboardMarkup:
        """Create confirmation keyboard for adding new asset."""
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirmar e Adicionar", callback_data="confirm_add_asset"),
                InlineKeyboardButton("❌ Cancelar", callback_data="cancel"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def confirm_or_correct_asset() -> InlineKeyboardMarkup:
        """Create keyboard with options to confirm or correct asset data."""
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirmar", callback_data="confirm_add_asset"),
            ],
            [
                InlineKeyboardButton("✏️ Corrigir Preço", callback_data="correct_price"),
                InlineKeyboardButton("✏️ Corrigir Investido", callback_data="correct_invested"),
            ],
            [
                InlineKeyboardButton("❌ Cancelar", callback_data="cancel"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def entries_list(asset_id: int, entries: List) -> InlineKeyboardMarkup:
        """Create keyboard for entries list."""
        keyboard = []
        for entry in entries[:5]:
            date_str = entry.entry_date.strftime("%d/%m/%y")
            keyboard.append([
                InlineKeyboardButton(
                    f"📅 {date_str} - ${entry.entry_price:,.2f} x {entry.quantity:,.4f}",
                    callback_data=f"entry_detail_{entry.id}"
                )
            ])
        keyboard.append([
            InlineKeyboardButton("➕ Nova Entrada", callback_data=f"add_entry_{asset_id}")
        ])
        keyboard.append([
            InlineKeyboardButton("🔙 Voltar ao Ativo", callback_data=f"asset_detail_{asset_id}")
        ])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def reserve_actions() -> InlineKeyboardMarkup:
        """Create keyboard for reserve status."""
        keyboard = [
            [InlineKeyboardButton("➕ Adicionar USDT", callback_data="add_usdt")],
            [InlineKeyboardButton("⚙️ Alterar Meta", callback_data="change_reserve_target")],
            [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def technical_analysis_menu() -> InlineKeyboardMarkup:
        """Create keyboard for technical analysis menu."""
        keyboard = [
            [InlineKeyboardButton("📊 Análise de Tendência", callback_data="trend_analysis_menu")],
            [InlineKeyboardButton("☠️ Death Cross Scanner", callback_data="scan_death_cross")],
            [InlineKeyboardButton("✨ Golden Cross Scanner", callback_data="scan_golden_cross")],
            [InlineKeyboardButton("📉 Ativos em Risco", callback_data="high_risk_assets")],
            [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def trend_analysis_menu() -> InlineKeyboardMarkup:
        """Create keyboard for trend analysis options."""
        keyboard = [
            [InlineKeyboardButton("📈 Analisar Meus Ativos (Spot)", callback_data="trend_portfolio")],
            [InlineKeyboardButton("📊 Analisar Trades Futuros", callback_data="trend_futures")],
            [InlineKeyboardButton("🔍 Analisar Ativo Específico", callback_data="trend_specific")],
            [InlineKeyboardButton("ℹ️ Sobre os Indicadores", callback_data="trend_info")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="technical_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def trend_timeframe_menu(action: str) -> InlineKeyboardMarkup:
        """Create keyboard for selecting timeframe."""
        keyboard = [
            [
                InlineKeyboardButton("1h", callback_data=f"trend_tf_{action}_1h"),
                InlineKeyboardButton("4h ⭐", callback_data=f"trend_tf_{action}_4h"),
                InlineKeyboardButton("1d ⭐", callback_data=f"trend_tf_{action}_1d"),
            ],
            [InlineKeyboardButton("🔙 Voltar", callback_data="trend_analysis_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def trend_asset_list(assets: list, asset_type: str = "spot") -> InlineKeyboardMarkup:
        """Create keyboard for selecting an asset to analyze."""
        keyboard = []
        for asset in assets[:15]:  # Max 15 assets
            asset_id = asset.get('id', 0)
            symbol = asset.get('symbol', 'N/A').upper()
            keyboard.append([
                InlineKeyboardButton(f"📊 {symbol}", callback_data=f"trend_asset_{asset_type}_{asset_id}")
            ])
        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="trend_analysis_menu")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def trend_analysis_actions(symbol: str) -> InlineKeyboardMarkup:
        """Create keyboard for actions after trend analysis."""
        keyboard = [
            [
                InlineKeyboardButton("⏱️ Outro Timeframe", callback_data=f"trend_change_tf_{symbol}"),
            ],
            [
                InlineKeyboardButton("🔄 Atualizar", callback_data=f"trend_refresh_{symbol}"),
            ],
            [InlineKeyboardButton("🔙 Voltar", callback_data="trend_analysis_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def death_cross_actions(asset_id: int) -> InlineKeyboardMarkup:
        """Create keyboard for death cross alert actions."""
        keyboard = [
            [
                InlineKeyboardButton("🔴 Vender Tudo", callback_data=f"sell_all_{asset_id}"),
                InlineKeyboardButton("🟡 Vender 50%", callback_data=f"sell_half_{asset_id}"),
            ],
            [InlineKeyboardButton("📊 Ver Análise", callback_data=f"full_analysis_{asset_id}")],
            [InlineKeyboardButton("⏸️ Manter", callback_data=f"hold_monitor_{asset_id}")],
        ]
        return InlineKeyboardMarkup(keyboard)

    # ==================== FUTURES KEYBOARDS ====================

    @staticmethod
    def futures_menu() -> InlineKeyboardMarkup:
        """Create futures trading main menu keyboard."""
        keyboard = [
            [InlineKeyboardButton("📈 Posições Abertas", callback_data="futures_open")],
            [InlineKeyboardButton("➕ Novo Trade", callback_data="futures_add")],
            [InlineKeyboardButton("📊 Histórico de Trades", callback_data="futures_history")],
            [InlineKeyboardButton("📉 Estatísticas", callback_data="futures_stats")],
            [InlineKeyboardButton("⚠️ Trades de Alto Risco", callback_data="futures_high_risk")],
            [InlineKeyboardButton("⚙️ Gerenciamento de Risco", callback_data="futures_risk_management")],
            [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def futures_risk_management_menu(futures_balance: float = 0.0, risk_percent: float = 5.0) -> InlineKeyboardMarkup:
        """Create risk management menu keyboard."""
        keyboard = [
            [InlineKeyboardButton("💰 Atualizar Saldo Futuros", callback_data="update_futures_balance")],
            [InlineKeyboardButton("⚙️ Configurar % de Risco", callback_data="set_futures_risk_percent")],
            [InlineKeyboardButton("📊 Ver Risco Atual", callback_data="futures_risk_status")],
            [InlineKeyboardButton("ℹ️ Como funciona o risco", callback_data="futures_risk_info")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="futures_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def futures_side_selection() -> InlineKeyboardMarkup:
        """Create keyboard for selecting trade side (long/short)."""
        keyboard = [
            [
                InlineKeyboardButton("🟢 LONG (Compra)", callback_data="futures_side_long"),
                InlineKeyboardButton("🔴 SHORT (Venda)", callback_data="futures_side_short"),
            ],
            [InlineKeyboardButton("❌ Cancelar", callback_data="futures_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    # Alias for backwards compatibility
    @staticmethod
    def futures_direction_selection() -> InlineKeyboardMarkup:
        """Alias for futures_side_selection."""
        return KeyboardBuilder.futures_side_selection()

    @staticmethod
    def futures_leverage_selection(is_altcoin: bool = False) -> InlineKeyboardMarkup:
        """Create keyboard for selecting leverage with risk info."""
        keyboard = [
            [
                InlineKeyboardButton("1x", callback_data="futures_lev_1"),
                InlineKeyboardButton("2x", callback_data="futures_lev_2"),
                InlineKeyboardButton("3x", callback_data="futures_lev_3"),
            ],
            [
                InlineKeyboardButton("5x ⚠️", callback_data="futures_lev_5"),
                InlineKeyboardButton("10x 🔴", callback_data="futures_lev_10"),
                InlineKeyboardButton("20x 💀", callback_data="futures_lev_20"),
            ],
            [InlineKeyboardButton("✏️ Outro valor", callback_data="futures_lev_custom")],
        ]
        
        if is_altcoin:
            keyboard.append([
                InlineKeyboardButton("⚠️ AVISO: Altcoin (>3x = Alto Risco)", callback_data="futures_risk_info")
            ])
        
        keyboard.append([
            InlineKeyboardButton("ℹ️ Sobre riscos de alavancagem", callback_data="futures_leverage_info")
        ])
        keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="futures_menu")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def futures_timeframe_selection() -> InlineKeyboardMarkup:
        """Create keyboard for selecting analysis timeframe."""
        keyboard = [
            [
                InlineKeyboardButton("15m", callback_data="futures_tf_15m"),
                InlineKeyboardButton("30m", callback_data="futures_tf_30m"),
                InlineKeyboardButton("1h", callback_data="futures_tf_1h"),
            ],
            [
                InlineKeyboardButton("4h ⭐", callback_data="futures_tf_4h"),
                InlineKeyboardButton("1d ⭐", callback_data="futures_tf_1d"),
                InlineKeyboardButton("1w", callback_data="futures_tf_1w"),
            ],
            [InlineKeyboardButton("❌ Cancelar", callback_data="futures_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def futures_targets_options(target_count: int = 0) -> InlineKeyboardMarkup:
        """Create keyboard for targets configuration.
        
        Args:
            target_count: Number of targets already added (optional)
        """
        keyboard = []
        
        # Only show add button if less than 3 targets
        if target_count < 3:
            keyboard.append([InlineKeyboardButton("➕ Adicionar mais um alvo", callback_data="futures_add_target")])
        
        keyboard.append([InlineKeyboardButton("✅ Concluir alvos", callback_data="futures_done_targets")])
        keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="futures_menu")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def futures_confirm_trade(show_risk_warning: bool = False) -> InlineKeyboardMarkup:
        """Create confirmation keyboard for new futures trade."""
        keyboard = []
        
        if show_risk_warning:
            keyboard.append([
                InlineKeyboardButton("⚠️ ALTO RISCO - Confirmar Mesmo Assim", callback_data="futures_confirm_risky")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("✅ Confirmar Trade", callback_data="futures_confirm")
            ])
        
        keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="futures_menu")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def futures_zone_check() -> InlineKeyboardMarkup:
        """Create keyboard for liquidity zone check prompt."""
        keyboard = [
            [
                InlineKeyboardButton("✅ Sim, verificar zonas", callback_data="futures_check_zones"),
                InlineKeyboardButton("❌ Não, prosseguir", callback_data="futures_skip_zones"),
            ],
            [InlineKeyboardButton("🔙 Cancelar", callback_data="futures_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def futures_zone_choice(zone_price: float = 0) -> InlineKeyboardMarkup:
        """Create keyboard for choosing between management stop and zone stop."""
        keyboard = [
            [InlineKeyboardButton("1️⃣ Stop do Gerenciamento", callback_data="futures_use_management_stop")],
            [InlineKeyboardButton("2️⃣ Stop na Zona de Liquidez", callback_data="futures_use_zone_stop")],
            [InlineKeyboardButton("🔙 Cancelar", callback_data="futures_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def futures_final_confirm(show_risk_warning: bool = False) -> InlineKeyboardMarkup:
        """Create final confirmation keyboard after risk management flow."""
        keyboard = []
        
        if show_risk_warning:
            keyboard.append([
                InlineKeyboardButton("⚠️ ALTO RISCO - Confirmar", callback_data="futures_final_confirm_risky")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("✅ Confirmar e Cadastrar", callback_data="futures_final_confirm")
            ])
        
        keyboard.append([
            InlineKeyboardButton("✏️ Ajustar Stop", callback_data="futures_adjust_stop"),
            InlineKeyboardButton("❌ Cancelar", callback_data="futures_menu"),
        ])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def futures_trade_actions(trade_id: int) -> InlineKeyboardMarkup:
        """Create keyboard for individual futures trade actions."""
        keyboard = [
            [
                InlineKeyboardButton("📊 Atualizar Preço", callback_data=f"futures_refresh_{trade_id}"),
                InlineKeyboardButton("📈 Ver Análise", callback_data=f"futures_analysis_{trade_id}"),
            ],
            [
                InlineKeyboardButton("✏️ Editar SL/TP", callback_data=f"futures_edit_sltp_{trade_id}"),
            ],
            [
                InlineKeyboardButton("🔴 Fechar Trade", callback_data=f"futures_close_{trade_id}"),
                InlineKeyboardButton("🗑️ Deletar", callback_data=f"futures_delete_{trade_id}"),
            ],
            [InlineKeyboardButton("🔙 Voltar às Posições", callback_data="futures_open")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def futures_close_confirm(trade_id: int) -> InlineKeyboardMarkup:
        """Create confirmation keyboard for closing a futures trade."""
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirmar Fechamento", callback_data=f"futures_close_confirm_{trade_id}"),
                InlineKeyboardButton("❌ Cancelar", callback_data=f"futures_detail_{trade_id}"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def futures_open_trades(trades: List) -> InlineKeyboardMarkup:
        """Create keyboard listing open futures trades."""
        keyboard = []
        for trade in trades[:10]:
            pnl = trade.unrealized_pnl or 0
            pnl_emoji = "🟢" if pnl >= 0 else "🔴"
            side_emoji = "📈" if trade.side == "long" else "📉"
            risk_emoji = "⚠️" if trade.risk_level in ["high", "extreme"] else ""
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{side_emoji} {trade.pair} {trade.leverage}x {pnl_emoji} {risk_emoji}",
                    callback_data=f"futures_detail_{trade.id}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("➕ Novo Trade", callback_data="futures_add")])
        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="futures_menu")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def futures_history_list(trades: List) -> InlineKeyboardMarkup:
        """Create keyboard for futures trade history."""
        keyboard = []
        for trade in trades[:10]:
            pnl = trade.pnl or 0
            pnl_emoji = "🟢" if pnl >= 0 else "🔴"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{pnl_emoji} {trade.pair} {trade.leverage}x | ${pnl:+,.2f}",
                    callback_data=f"futures_history_detail_{trade.id}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="futures_menu")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def risk_panel_actions() -> InlineKeyboardMarkup:
        """Create keyboard for risk panel."""
        keyboard = [
            [InlineKeyboardButton("📊 Ver Carteira", callback_data="portfolio")],
            [InlineKeyboardButton("📈 Ver Futuros", callback_data="futures_open")],
            [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    # ==================== CADASTRO KEYBOARDS ====================

    @staticmethod
    def accept_terms() -> InlineKeyboardMarkup:
        """Create keyboard for accepting terms."""
        keyboard = [
            [InlineKeyboardButton("✅ Aceito os Termos", callback_data="accept_terms")],
            [InlineKeyboardButton("❌ Não Aceito", callback_data="reject_terms")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def continue_registration() -> InlineKeyboardMarkup:
        """Create continue button for registration."""
        keyboard = [
            [InlineKeyboardButton("➡️ Continuar", callback_data="continue_registration")],
        ]
        return InlineKeyboardMarkup(keyboard)

    # ==================== ADMIN KEYBOARDS ====================

    @staticmethod
    def admin_panel() -> InlineKeyboardMarkup:
        """Create admin panel keyboard."""
        keyboard = [
            [InlineKeyboardButton("👥 Consultar Usuários", callback_data="admin_users")],
            [InlineKeyboardButton("📊 Gerar Relatório", callback_data="admin_report")],
            [
                InlineKeyboardButton("🔗 Link Convite User", callback_data="admin_invite_user"),
                InlineKeyboardButton("🔐 Link Convite Admin", callback_data="admin_invite_admin"),
            ],
            [InlineKeyboardButton("🚫 Banir Usuário", callback_data="admin_ban")],
            [InlineKeyboardButton("✅ Desbanir Usuário", callback_data="admin_unban")],
            [InlineKeyboardButton("📜 Logs de Admin", callback_data="admin_logs")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="settings")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def admin_users_list(users: List, page: int = 0, per_page: int = 10) -> InlineKeyboardMarkup:
        """Create keyboard for user list in admin panel."""
        keyboard = []
        start = page * per_page
        end = start + per_page
        
        for user in users[start:end]:
            status = "🟢" if not user.is_banned else "🔴"
            admin_badge = "👑" if user.is_admin else ""
            keyboard.append([
                InlineKeyboardButton(
                    f"{status} #{user.registration_number} {user.full_name or user.first_name} {admin_badge}",
                    callback_data=f"admin_user_detail_{user.id}"
                )
            ])
        
        # Pagination
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"admin_users_page_{page-1}"))
        if end < len(users):
            nav_buttons.append(InlineKeyboardButton("➡️ Próximo", callback_data=f"admin_users_page_{page+1}"))
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="admin_panel")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def admin_user_actions(user_id: int, is_banned: bool, is_admin: bool) -> InlineKeyboardMarkup:
        """Create keyboard for user actions in admin panel."""
        keyboard = []
        
        if is_banned:
            keyboard.append([InlineKeyboardButton("✅ Desbanir", callback_data=f"admin_unban_{user_id}")])
        else:
            keyboard.append([InlineKeyboardButton("🚫 Banir", callback_data=f"admin_ban_{user_id}")])
        
        if not is_admin:
            keyboard.append([InlineKeyboardButton("👑 Tornar Admin", callback_data=f"admin_make_admin_{user_id}")])
        else:
            keyboard.append([InlineKeyboardButton("👤 Remover Admin", callback_data=f"admin_remove_admin_{user_id}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="admin_users")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def futures_close_confirm_trade(trade_id: int) -> InlineKeyboardMarkup:
        """Create keyboard to confirm closing a futures trade from alert."""
        keyboard = [
            [
                InlineKeyboardButton("✅ Sim, Fechar", callback_data=f"futures_close_confirm_{trade_id}"),
                InlineKeyboardButton("❌ Não, Manter", callback_data=f"futures_keep_open_{trade_id}"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

