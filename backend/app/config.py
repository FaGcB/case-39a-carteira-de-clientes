from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/carteira"

    tamanho_lote: int = 200
    lease_segundos: int = 60
    max_tentativas: int = 5
    intervalo_worker_segundos: float = 1.0
    tamanho_maximo_arquivo_mb: int = 20

    motor_limite_por_minuto: int = 10

    cors_origens: list[str] = ["http://localhost:5173", "http://localhost:8080"]


config = Config()
