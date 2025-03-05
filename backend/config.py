from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str

    # instagram
    instagram_score_url: str
    instagram_multiprompt: str
    # facebook
    facebook_score_url: str
    facebook_multiprompt: str

    echo_sql: bool = True
    test: bool = False
    project_name: str = "Social Parser API"
    debug_logs: bool = False

settings = Settings()  # type: ignore