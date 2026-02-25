from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str = Field(min_length=11, max_length=32)
    password: str = Field(min_length=1, max_length=128)


class LoginData(BaseModel):
    accessToken: str
    refreshToken: str
    tokenType: str = "Bearer"
    staffId: str
    name: str
    role: str
    phone: str
    mustChangePassword: bool = False


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(alias="refreshToken", min_length=1)


class RefreshData(BaseModel):
    accessToken: str
    refreshToken: str
    tokenType: str = "Bearer"
    staffId: str
    name: str
    role: str
    phone: str
    mustChangePassword: bool = False


class LogoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(alias="refreshToken", min_length=1)


class MeData(BaseModel):
    staffId: str
    name: str
    phone: str
    role: str
    mustChangePassword: bool = False


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    currentPassword: str = Field(min_length=1, max_length=128)
    newPassword: str = Field(min_length=8, max_length=128)
