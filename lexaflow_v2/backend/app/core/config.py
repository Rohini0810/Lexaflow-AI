from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "LexaFlow AI v2"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./data/lexaflow_v2.db"

    azure_doc_intelligence_endpoint: str | None = None
    azure_doc_intelligence_key: str | None = None

    azure_openai_endpoint: str | None = None
    azure_openai_key: str | None = None
    azure_openai_deployment: str | None = None
    azure_openai_api_version: str = "2024-05-01-preview"

    monitored_regulation_id: str = "RBI_KYC_001"
    monitored_regulation_title: str = "RBI KYC Master Direction Update"
    monitored_source: str = "RBI"
    monitored_jurisdiction: str = "India"
    old_doc_path: str = "./data/sample_docs/rbi_v1.pdf"
    new_doc_path: str = "./data/sample_docs/rbi_v2.pdf"


settings = Settings()

