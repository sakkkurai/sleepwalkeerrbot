from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

version = 2.00

class Settings(BaseSettings):
    
    BOT_TOKEN: SecretStr
    BOT_USERNAME: str

    CHANNEL_ID: int
    CHANNEL_USERNAME: str

    DISCUSSION_CHAT_ID: int
    MODERATION_CHAT_ID: int
    
    ADMIN_IDS: str
    DB_URL: str

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    def get_admin_ids(self) -> list[int]:
        return [int(admin_id) for admin_id in self.ADMIN_IDS.split(',')]

config = Settings()