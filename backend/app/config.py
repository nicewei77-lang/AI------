from pydantic_settings import BaseSettings, SettingsConfigDict

# 상속할 부모 클래스
class Settings(BaseSettings):
    # 데이터를 받을 필드: type hint
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_algorism: str = "HS256"
    backend_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    backend_cors_origin_regex: str | None = r"https://.*\.vercel\.app"
    openai_api_key: str | None = None
    agent_model: str = "gpt-5.5"
    reasoning_effort: str = "medium"
    embedding_model: str = "text-embedding-3-small"
    rag_top_k: int = 3
    rag_similarity_threshold: float = 0.18
    rag_min_indexed_posts: int = 2
    rag_weighted_min_indexed_posts: int = 20
    rag_weighted_candidate_multiplier: int = 4
    agent_max_turns: int = 10
    mcp_server_url: str | None = None
    mcp_server_command: str | None = None
    mcp_request_timeout_seconds: float = 5.0
    mcp_body_size_limit_bytes: int = 1_500_000
    mcp_main_text_limit_chars: int = 4_000
    mcp_site_context_max_pages: int = 5
    mcp_site_context_text_limit_chars: int = 12_000
    mcp_site_context_timeout_seconds: float = 15.0
    mcp_rendered_timeout_seconds: float = 12.0
    mcp_rendered_text_limit_chars: int = 4_000
    mcp_screenshot_timeout_seconds: float = 10.0
    mcp_lighthouse_timeout_seconds: float = 25.0
    mcp_github_readme_limit_chars: int = 6_000
    mcp_max_links: int = 20
    mcp_max_redirects: int = 5

    def cors_origins(self) -> list[str]:
        return [
            origin.rstrip("/")
            for origin in (item.strip() for item in self.backend_cors_origins.split(","))
            if origin
        ]
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
# 다른 곳에서 쓸 객체 인스턴스 만들기
settings = Settings()
