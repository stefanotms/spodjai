import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    spotify_client_id: str = "PON_AQUI_TU_CLIENT_ID"
    spotify_client_secret: str = "PON_AQUI_TU_CLIENT_SECRET"
    spotify_redirect_uri: str = "http://localhost:8000/callback"
    gemini_api_key: str = ""
    port: int = 8000
    host: str = "0.0.0.0"

    # Configuración para leer desde un archivo .env si existe
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
