from pydantic_settings import BaseSettings, SettingsConfigDict


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


settings = Settings()
