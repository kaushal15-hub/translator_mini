from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    app_name: str = "Translator Platform"
    secret_key: str = "CHANGE-ME-IN-ENVIRONMENT"
    algorithm: str = "HS256"
    access_token_minutes: int = 60 * 8
    database_url: str = "sqlite:///./translator.db"
    cors_origins: str = "http://localhost:5173"
    redis_url: str = "redis://localhost:6379/0"
    translation_mode: str = "development"
    model_name: str = "ai4bharat/indictrans2-indic-en-dist-200M"
    model_cache_dir: str = "./models"
    inference_queue_size: int = 32
    model_max_length: int = 256
    model_threads: int = 4
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
settings = Settings()
