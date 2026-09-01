from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str
    embedding_model: str

    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int

    database_url: str

    pdf_upload_path: str
    chroma_db_path: str

    max_retry_count: int
    retrieval_top_k: int

    class Config:
        env_file = ".env"


settings = Settings()