from pydantic_settings import BaseSettings, SettingsConfigDict

# 상속할 부모 클래스
class Settings(BaseSettings):
    # 데이터를 받을 필드: type hint
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_algorism: str = "HS256"
    openai_api_key: str | None = None
    agent_model: str = "gpt-5.5"
    reasoning_effort: str = "medium"
    embedding_model: str = "text-embedding-3-small"
    mcp_server_url: str | None = None
    mcp_server_command: str | None = None
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
# 다른 곳에서 쓸 객체 인스턴스 만들기
settings = Settings()
