"""
Database models for the Crypto Portfolio Bot.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, BigInteger, Text
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class User(Base):
    """User model for storing Telegram user information."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    
    # Cadastro obrigatório
    registration_number = Column(Integer, unique=True, nullable=True)  # Numeração sequencial
    full_name = Column(String(255), nullable=True)  # Nome completo cadastrado
    phone = Column(String(50), nullable=True)  # Telefone
    birth_date = Column(String(20), nullable=True)  # Data de nascimento
    is_registered = Column(Boolean, default=False)  # Cadastro completo
    accepted_terms = Column(Boolean, default=False)  # Aceitou termos de uso
    accepted_terms_at = Column(DateTime, nullable=True)  # Data do aceite
    
    # Carteira de Futuros
    futures_balance = Column(Float, default=0.0)  # Saldo disponível para futuros
    futures_risk_percent = Column(Float, default=5.0)  # % de risco por trade (padrão 5%)
    
    # Admin e controle
    is_admin = Column(Boolean, default=False)  # É administrador
    is_banned = Column(Boolean, default=False)  # Usuário banido
    banned_at = Column(DateTime, nullable=True)
    banned_by = Column(Integer, nullable=True)  # ID do admin que baniu
    invited_by = Column(Integer, nullable=True)  # ID de quem convidou
    invite_code = Column(String(50), nullable=True)  # Código de convite usado
    referral = Column(String(255), nullable=True)  # Quem indicou o usuário (texto livre)
    
    coingecko_portfolio_id = Column(String(255), nullable=True)
    coingecko_api_key = Column(String(255), nullable=True)
    usdt_reserve = Column(Float, default=0.0)  # USDT reserve balance
    reserve_target_percent = Column(Float, default=15.0)  # Target reserve percentage
    is_active = Column(Boolean, default=True)
    notifications_enabled = Column(Boolean, default=True)
    death_cross_alerts = Column(Boolean, default=True)  # Enable death cross alerts
    
    # Configurações de alertas personalizados
    price_alerts_enabled = Column(Boolean, default=True)  # Alertas de preço dos ativos on/off
    check_interval_minutes = Column(Integer, default=5)  # Intervalo de verificação (5, 10, 30, 60)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assets = relationship("Asset", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    entries = relationship("AssetEntry", back_populates="user", cascade="all, delete-orphan")
    futures_trades = relationship("FuturesTrade", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"

    @property
    def total_invested(self) -> float:
        """Calculate total invested across all assets."""
        return sum(asset.total_invested for asset in self.assets if asset.is_active)

    @property
    def recommended_reserve(self) -> float:
        """Calculate recommended USDT reserve."""
        return self.total_invested * (self.reserve_target_percent / 100)


class Asset(Base):
    """Asset model for storing user's crypto assets."""
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    coin_id = Column(String(100), nullable=False)  # Coin ID (e.g., 'btc', 'eth')
    symbol = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False, default=0.0)
    average_price = Column(Float, nullable=False, default=0.0)  # Calculated average price
    current_price = Column(Float, nullable=True)
    last_alert_price = Column(Float, nullable=True)
    total_invested = Column(Float, nullable=False, default=0.0)
    times_averaged = Column(Integer, default=0)
    times_sold_partial = Column(Integer, default=0)
    has_death_cross = Column(Boolean, default=False)  # Track death cross status
    last_death_cross_alert = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    is_confirmed = Column(Boolean, default=False)  # User confirmed to add to portfolio
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="assets")
    entries = relationship("AssetEntry", back_populates="asset", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Asset(id={self.id}, coin_id={self.coin_id}, symbol={self.symbol})>"

    @property
    def purchase_price(self) -> float:
        """Alias for average_price for backward compatibility."""
        return self.average_price or 0.0

    @property
    def profit_loss_percent(self) -> Optional[float]:
        """Calculate current profit/loss percentage."""
        if self.current_price and self.average_price and self.average_price > 0:
            return ((self.current_price - self.average_price) / self.average_price) * 100
        return None

    @property
    def total_value(self) -> Optional[float]:
        """Calculate total current value."""
        if self.current_price and self.quantity:
            return self.current_price * self.quantity
        return None

    @property
    def profit_loss_usd(self) -> Optional[float]:
        """Calculate profit/loss in USD."""
        if self.total_value is not None:
            return self.total_value - self.total_invested
        return None

    def recalculate_average(self):
        """Recalculate average price from all entries."""
        active_entries = [e for e in self.entries if e.is_active]
        if not active_entries:
            self.average_price = 0
            self.quantity = 0
            self.total_invested = 0
            return
        
        total_qty = sum(e.quantity for e in active_entries)
        total_cost = sum(e.quantity * e.entry_price for e in active_entries)
        
        self.quantity = total_qty
        self.total_invested = total_cost
        self.average_price = total_cost / total_qty if total_qty > 0 else 0


class AssetEntry(Base):
    """Individual buy entry for an asset (supports multiple entries)."""
    __tablename__ = "asset_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    entry_price = Column(Float, nullable=False)  # Price at which bought
    quantity = Column(Float, nullable=False)  # Quantity bought
    total_value = Column(Float, nullable=False)  # Total USD value (entry_price * quantity)
    entry_date = Column(DateTime, default=datetime.utcnow)  # Date of purchase
    notes = Column(Text, nullable=True)  # Optional notes
    is_active = Column(Boolean, default=True)  # Can be deactivated when sold
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="entries")
    asset = relationship("Asset", back_populates="entries")

    def __repr__(self):
        return f"<AssetEntry(id={self.id}, asset_id={self.asset_id}, qty={self.quantity}, price={self.entry_price})>"

    @property
    def current_value(self) -> Optional[float]:
        """Calculate current value based on asset's current price."""
        if self.asset and self.asset.current_price:
            return self.quantity * self.asset.current_price
        return None

    @property
    def profit_loss(self) -> Optional[float]:
        """Calculate profit/loss for this entry."""
        current = self.current_value
        if current is not None:
            return current - self.total_value
        return None

    @property
    def profit_loss_percent(self) -> Optional[float]:
        """Calculate profit/loss percentage for this entry."""
        if self.asset and self.asset.current_price and self.entry_price > 0:
            return ((self.asset.current_price - self.entry_price) / self.entry_price) * 100
        return None


class Alert(Base):
    """Alert model for storing sent alerts history."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    alert_type = Column(String(50), nullable=False)  # 'drop_30', 'profit_100', 'death_cross', 'reserve', 'info'
    message = Column(String(2000), nullable=False)
    price_at_alert = Column(Float, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="alerts")

    def __repr__(self):
        return f"<Alert(id={self.id}, type={self.alert_type})>"


class PriceHistory(Base):
    """Price history model for tracking asset prices over time."""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    price = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PriceHistory(asset_id={self.asset_id}, price={self.price})>"


class FuturesTrade(Base):
    """Futures trade model for storing leveraged trading positions."""
    __tablename__ = "futures_trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String(20), nullable=False)  # Base symbol e.g., BTC, ETH
    pair = Column(String(50), nullable=False)  # e.g., BTCUSDT, ETHUSDT
    direction = Column(String(10), nullable=False)  # 'long' or 'short' (alias for side)
    side = Column(String(10), nullable=True)  # 'long' or 'short'
    leverage = Column(Integer, nullable=False, default=1)  # Leverage multiplier
    entry_price = Column(Float, nullable=False)  # Entry price
    quantity = Column(Float, nullable=False)  # Position size in contracts/coins
    margin = Column(Float, nullable=False)  # Margin used (collateral)
    stop_loss = Column(Float, nullable=True)  # Stop loss price
    take_profit = Column(Float, nullable=True)  # Take profit price
    current_price = Column(Float, nullable=True)  # Current market price
    status = Column(String(20), default="open")  # 'open', 'closed', 'liquidated'
    pnl = Column(Float, nullable=True)  # Realized P&L when closed
    pnl_percent = Column(Float, nullable=True)  # P&L percentage when closed
    is_altcoin = Column(Boolean, default=False)  # True if not BTC/ETH
    risk_level = Column(String(20), default="normal")  # 'normal', 'high', 'extreme'
    
    # Risk Management fields
    stop_percent = Column(Float, nullable=True)  # Stop loss em %
    risk_usd = Column(Float, nullable=True)  # Risco em USDT neste trade
    timeframe = Column(String(10), nullable=True)  # Timeframe usado na análise (ex: 1h, 4h)
    zone_used = Column(String(20), nullable=True)  # 'management' ou 'zone'
    
    # Alvos de venda (targets) - JSON serializado como string
    target_1_price = Column(Float, nullable=True)  # Preço alvo 1
    target_1_percent = Column(Float, nullable=True)  # % a vender no alvo 1
    target_2_price = Column(Float, nullable=True)  # Preço alvo 2
    target_2_percent = Column(Float, nullable=True)  # % a vender no alvo 2
    target_3_price = Column(Float, nullable=True)  # Preço alvo 3
    target_3_percent = Column(Float, nullable=True)  # % a vender no alvo 3
    
    # Alocação do patrimônio
    allocation_percent = Column(Float, nullable=True)  # % do patrimônio alocado neste trade
    
    notes = Column(Text, nullable=True)  # Optional notes
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="futures_trades")

    def __repr__(self):
        return f"<FuturesTrade(id={self.id}, pair={self.pair}, side={self.side}, leverage={self.leverage}x)>"

    @property
    def base_symbol(self) -> str:
        """Get base symbol from pair (e.g., BTC from BTCUSDT)."""
        return self.pair.replace("USDT", "").replace("USD", "")

    @property
    def position_value(self) -> float:
        """Calculate total position value."""
        return self.quantity * self.entry_price

    @property
    def leveraged_value(self) -> float:
        """Calculate leveraged position value."""
        return self.position_value * self.leverage

    @property
    def unrealized_pnl(self) -> Optional[float]:
        """Calculate unrealized P&L for open positions."""
        if self.status != "open" or not self.current_price:
            return None
        
        price_diff = self.current_price - self.entry_price
        if self.side == "short":
            price_diff = -price_diff
        
        return price_diff * self.quantity * self.leverage

    @property
    def unrealized_pnl_percent(self) -> Optional[float]:
        """Calculate unrealized P&L percentage."""
        if self.status != "open" or not self.current_price or self.entry_price == 0:
            return None
        
        if self.side == "long":
            return ((self.current_price - self.entry_price) / self.entry_price) * 100 * self.leverage
        else:  # short
            return ((self.entry_price - self.current_price) / self.entry_price) * 100 * self.leverage

    @property
    def liquidation_price(self) -> Optional[float]:
        """
        Calcula preço de liquidação para margem isolada (Isolated Margin).
        
        Fórmula:
          Para LONG:  liq_price = entry_price - (initial_margin - maint_margin) / quantity
          Para SHORT: liq_price = entry_price + (initial_margin - maint_margin) / quantity
        
        Onde:
          - initial_margin: Margem colocada (self.margin)
          - maint_margin: Notional * MMR (Maintenance Margin Rate ~0.5%)
          - quantity: Quantidade do ativo
          - notional: entry_price * quantity
        """
        if self.leverage <= 0 or not self.margin or not self.quantity:
            return None
        
        # Maintenance Margin Rate (aproximado 0.5% para posições médias)
        # Varia por tier na corretora, mas 0.5% é comum
        mmr = 0.005
        
        # Notional value (valor total da posição)
        notional = self.entry_price * self.quantity
        
        # Margem de manutenção
        maintenance_margin = notional * mmr
        
        # Margem sustentável (quanto o preço pode andar contra)
        sustainable_margin = self.margin - maintenance_margin
        
        if sustainable_margin <= 0:
            return self.entry_price  # Já liquidado ou impossível
        
        # Ajuste de preço baseado na margem sustentável
        price_adjust = sustainable_margin / self.quantity
        
        if self.side == "long":
            liq_price = self.entry_price - price_adjust
        else:  # short
            liq_price = self.entry_price + price_adjust
        
        # Ajuste por fees de fechamento (~0.05%)
        fee_approx = notional * 0.0005
        fee_adjust = fee_approx / self.quantity
        
        if self.side == "long":
            liq_price += fee_adjust  # Para long, fees pioram (liq mais alta)
        else:
            liq_price -= fee_adjust  # Para short, fees pioram (liq mais baixa)
        
        return round(liq_price, 2)

    def calculate_risk_level(self) -> str:
        """Calculate risk level based on leverage and coin type."""
        if self.leverage >= 10:
            return "extreme"
        elif self.leverage > 3 and self.is_altcoin:
            return "high"
        elif self.leverage > 5:
            return "high"
        return "normal"

    def close_trade(self, close_price: float):
        """Close the trade and calculate final P&L."""
        price_diff = close_price - self.entry_price
        if self.side == "short":
            price_diff = -price_diff
        
        self.pnl = price_diff * self.quantity * self.leverage
        self.pnl_percent = (price_diff / self.entry_price) * 100 * self.leverage
        self.current_price = close_price
        self.status = "closed"
        self.closed_at = datetime.utcnow()


class InviteCode(Base):
    """Invite codes for new users."""
    __tablename__ = "invite_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    invite_type = Column(String(20), default="user")  # 'user' or 'admin'
    uses_count = Column(Integer, default=0)  # Number of times used
    max_uses = Column(Integer, nullable=True)  # Null = unlimited
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<InviteCode(code={self.code}, type={self.invite_type})>"


class ReserveAllocation(Base):
    """Track USDT reserve allocations when buying assets or averaging down."""
    __tablename__ = "reserve_allocations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)  # Target asset (null for deposits)
    allocation_type = Column(String(50), nullable=False)  # 'deposit', 'new_asset', 'average_down', 'withdrawal'
    amount = Column(Float, nullable=False)  # USDT amount allocated
    asset_symbol = Column(String(20), nullable=True)  # Target asset symbol
    asset_quantity = Column(Float, nullable=True)  # Quantity of target asset bought
    asset_price = Column(Float, nullable=True)  # Price at which asset was bought
    notes = Column(Text, nullable=True)  # Description of allocation
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ReserveAllocation(id={self.id}, type={self.allocation_type}, amount={self.amount})>"


class AdminLog(Base):
    """Log of admin actions."""
    __tablename__ = "admin_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)  # 'ban_user', 'unban_user', 'add_admin', 'create_invite'
    target_user_id = Column(Integer, nullable=True)  # User affected
    details = Column(Text, nullable=True)  # Additional details
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AdminLog(admin_id={self.admin_id}, action={self.action})>"
