import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr, Field

class Settings(BaseSettings):
    # SMTP Configuration
    MAIL_USERNAME: str = Field(default="")
    MAIL_PASSWORD: str = Field(default="")
    MAIL_FROM: str = Field(default="")
    MAIL_PORT: int = Field(default=587)
    MAIL_SERVER: str = Field(default="smtp.gmail.com")
    MAIL_STARTTLS: bool = Field(default=True)
    MAIL_SSL_TLS: bool = Field(default=False)
    
    # Provider selection: smtp, sendgrid, mailgun, aws_ses etc.
    EMAIL_PROVIDER: str = Field(default="smtp")
    
    # App Settings
    APP_NAME: str = Field(default="Email Sender Service")
    DEBUG: bool = Field(default=True)
    
    # Base directory
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Logs directory
    LOGS_DIR: str = Field(default="")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def __init__(self, **values):
        super().__init__(**values)
        if not self.LOGS_DIR:
            self.LOGS_DIR = os.path.join(self.BASE_DIR, "logs")
        os.makedirs(self.LOGS_DIR, exist_ok=True)
        # Create dynamic folder for uploads too
        os.makedirs(os.path.join(self.BASE_DIR, "uploads"), exist_ok=True)

settings = Settings()
