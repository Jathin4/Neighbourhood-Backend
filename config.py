import configparser
import pathlib

from pydantic_settings import BaseSettings, SettingsConfigDict

_INI_PATH = pathlib.Path(__file__).resolve().parent / "config_file" / "webconfig.ini"


def _dsn_from_ini() -> str | None:
    """config_file/webconfig.ini (gitignored) is the preferred local source for DB
    credentials — DATABASE_URL/MIGRATION_DATABASE_URL in .env are the fallback
    for a checkout that hasn't set it up yet."""
    if not _INI_PATH.exists():
        return None
    parser = configparser.ConfigParser()
    parser.read(_INI_PATH)
    if "database" not in parser:
        return None
    db = parser["database"]
    return f"postgresql://{db['user']}:{db['password']}@{db['host']}:{db.get('port', '5432')}/{db.get('dbname', 'postgres')}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    node_env: str = "development"
    port: int = 4000
    cors_origin: str = "*"

    database_url: str
    migration_database_url: str | None = None

    jwt_access_secret: str
    jwt_access_ttl_minutes: int = 15

    sms_gateway_base_url: str = ""
    sms_api_key: str = ""
    sms_sender_id: str = ""
    sms_entity_id: str = ""
    sms_template_id: str = ""
    sms_template: str = "Your OTP is {otp}"

    dev_expose_otp: bool = False

    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""


_ini_dsn = _dsn_from_ini()
settings = Settings(**({"database_url": _ini_dsn, "migration_database_url": _ini_dsn} if _ini_dsn else {}))
