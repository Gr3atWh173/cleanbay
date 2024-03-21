"""Contains the app settings"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Loads and represents app config from environment variables.

    Attributes:
      plugins_directory (str): The directory where plugin files are stored
      cache_size (int): Size for the cache
      cache_timeout (int): How long the cache maintains an entry (in seconds)
      session_timeout (int): Timeout for requests to external services (in seconds)
      rate_limit (str): Rate limit descriptor
      allowed_origin (str): Origin from which requests are allowed

    """

    plugins_directory: str = "./cleanbay/plugins"
    cache_size: int = 128
    cache_timeout: int = 300
    session_timeout: int = 8
    rate_limit: str = "100/minute"
    allowed_origin: str = "*"


settings = Settings()
