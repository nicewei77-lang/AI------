from pydantic_settings import BaseSettings, SettingsConfigDict

# 상속할 부모 클래스
class Settings(BaseSettings):
    # 데이터를 받을 필드: type hint
    database_url: str
    jwt_secret: str
    
    model_config = SettingsConfigDict(env_file=".env")
# 다른 곳에서 쓸 객체 인스턴스 만들기
settings = Settings()