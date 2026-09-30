from pydantic import BaseModel, Field


class SendOtpBody(BaseModel):
    phone: str = Field(min_length=8, max_length=20)


class VerifyOtpBody(BaseModel):
    phone: str = Field(min_length=8, max_length=20)
    otp: str = Field(min_length=4, max_length=6)


class RefreshBody(BaseModel):
    refresh_token: str = Field(min_length=10)


class FcmTokenBody(BaseModel):
    fcm_token: str = Field(min_length=1)


class ChangePhoneBody(BaseModel):
    new_phone: str = Field(min_length=8, max_length=20)
    otp: str = Field(min_length=4, max_length=6)
