from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    server_host: str
    server_port: int


settings = Settings(_env_file=".env", _env_file_encoding="utf-8")