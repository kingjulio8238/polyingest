from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # Application
    app_name: str = "PolyIngest"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # Polymarket API
    polymarket_api_key: Optional[str] = None
    polymarket_graphql_url: str = "https://clob.polymarket.com/graphql"
    polymarket_rest_url: str = "https://clob.polymarket.com"
    
    # Blockchain
    polygon_rpc_url: str
    polygon_archive_url: Optional[str] = None
    etherscan_api_key: Optional[str] = None
    
    # Storage
    redis_url: str = "redis://localhost:6379/0"
    database_url: str
    
    # Agent Configuration
    agent_vote_threshold: float = 0.6
    min_portfolio_ratio: float = 0.1
    min_success_rate: float = 0.7
    min_trade_history: int = 10
    
    # Performance
    rate_limit_per_minute: int = 100
    cache_ttl_seconds: int = 300
    max_concurrent_requests: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()