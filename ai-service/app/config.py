from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str
    embedding_model: str

    chroma_db_path: str

    max_retry_count: int
    retrieval_top_k: int

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
