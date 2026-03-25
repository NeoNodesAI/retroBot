"""Application settings and configuration."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # LLM Provider
    llm_provider: str = "anthropic"  # Options: openai, anthropic, gemini
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    
    # Model Configuration
    default_model: str = "claude-sonnet-4-5-20250929"
    fast_model: str = "claude-sonnet-4-5-20250929"
    enable_hybrid_models: bool = False
    
    # LangSmith (Optional)
    langsmith_api_key: Optional[str] = None
    langsmith_project: Optional[str] = None
    
    # Web Search APIs
    serper_api_key: Optional[str] = None
    google_search_api_key: Optional[str] = None
    google_search_engine_id: Optional[str] = None
    
    # Crypto Exchange APIs (Top 3 by Volume)
    binance_api_key: Optional[str] = None
    binance_api_secret: Optional[str] = None
    coinbase_api_key: Optional[str] = None
    coinbase_api_secret: Optional[str] = None
    kraken_api_key: Optional[str] = None
    kraken_api_secret: Optional[str] = None
    
    # On-chain / Base Mainnet
    agent_private_key: Optional[str] = None
    agent_contract_address: str = "0x52B6159BAAddB249fa5b913A46B161930284Dad3"
    base_rpc_url: str = "https://mainnet.base.org"

    # Database
    database_url: Optional[str] = None
    redis_url: Optional[str] = None
    
    # Agent Configuration
    agent_name: str = "retroBot"
    agent_version: str = "1.0.0"
    agent_description: str = "NeoNodes AI agent with LangGraph Cloud API and real-time crypto data"
    
    # Performance Settings
    max_tokens: int = 1500
    temperature: float = 0.3
    streaming_enabled: bool = True
    
    # Cache Settings
    cache_ttl: int = 300  # 5 minutes
    cache_max_size: int = 1000
    
    # Timeout Settings
    api_timeout: int = 30
    database_timeout: int = 5
    agent_timeout: float = 60.0
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Debug Mode
    debug_mode: bool = False
    
    class Config:
        env_file = [".env", "/root/testbot/.env"]
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()

