from src.app.utils.abstract_schemas import AbstractSettings
from pydantic import AnyHttpUrl, EmailStr


class DatabaseSettings(AbstractSettings):
    db_host_: str
    db_port: int
    db_name: str
    db_username: str
    db_password: str


class RedisConfig(AbstractSettings):
    host: str
    port: int
    db: int


class SlackSettings(AbstractSettings):
    access_token: str
    standup_token: str


# MAIL CONFIG
class MailSettings(AbstractSettings):
    mail_username: str
    mail_password: str
    mail_server: str
    mail_port: int
    mail_tls: bool
    mail_ssl: bool
    mail_from: EmailStr
    mail_from_name: str
    not_test_mail: bool = False


slack_settings = SlackSettings()
redis_settings = RedisConfig()
database_settings = DatabaseSettings()
mail_settings = MailSettings()
