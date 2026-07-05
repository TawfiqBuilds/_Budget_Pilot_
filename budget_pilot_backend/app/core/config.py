from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All configuration lives here, loaded from environment variables (.env locally,
    Render's environment variables in production). Nothing sensitive is hardcoded.
    """

    database_url: str
    supabase_url: str
    supabase_jwt_secret: str
    supabase_service_role_key: str
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
