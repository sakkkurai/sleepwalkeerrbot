from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

version = 2.6

class Settings(BaseSettings):

    BOT_TOKEN: SecretStr
    BOT_USERNAME: str

    CHANNEL_ID: int
    CHANNEL_USERNAME: str

    DISCUSSION_CHAT_ID: int
    MODERATION_CHAT_ID: int

    ADMIN_ID: int
    DB_URL: str

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

config = Settings()
