"""
Configuration settings for the Crypto Portfolio Bot.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class TelegramConfig(BaseModel):
    """Telegram bot configuration."""
    bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")


class OKXConfig(BaseModel):
    """OKX API configuration."""
    api_key: str = os.getenv("OKX_API_KEY", "")
    secret_key: str = os.getenv("OKX_SECRET_KEY", "")
    passphrase: str = os.getenv("OKX_PASSPHRASE", "")
    base_url: str = "https://www.okx.com"


class CoinGeckoConfig(BaseModel):
    """CoinGecko API configuration (legacy)."""
    api_key: str = os.getenv("COINGECKO_API_KEY", "")
    base_url: str = "https://api.coingecko.com/api/v3"
    pro_base_url: str = "https://pro-api.coingecko.com/api/v3"


class DatabaseConfig(BaseModel):
    """Database configuration."""
    url: str = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{BASE_DIR}/data/crypto_portfolio.db")


class MonitoringConfig(BaseModel):
    """Price monitoring configuration."""
    check_interval_minutes: int = int(os.getenv("PRICE_CHECK_INTERVAL_MINUTES", "5"))
    drop_threshold_percent: float = float(os.getenv("DROP_THRESHOLD_PERCENT", "30"))
    profit_threshold_percent: float = float(os.getenv("PROFIT_THRESHOLD_PERCENT", "100"))
    sell_recommendation_percent: float = float(os.getenv("SELL_RECOMMENDATION_PERCENT", "50"))
    reserve_percent: float = float(os.getenv("RESERVE_PERCENT", "15"))


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = os.getenv("LOG_LEVEL", "INFO")
    log_dir: Path = BASE_DIR / "logs"


class Settings(BaseModel):
    """Application settings."""
    telegram: TelegramConfig = TelegramConfig()
    okx: OKXConfig = OKXConfig()
    coingecko: CoinGeckoConfig = CoinGeckoConfig()
    database: DatabaseConfig = DatabaseConfig()
    monitoring: MonitoringConfig = MonitoringConfig()
    logging: LoggingConfig = LoggingConfig()


# Global settings instance
settings = Settings()
