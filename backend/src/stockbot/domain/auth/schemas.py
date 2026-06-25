"""Request/response models for the auth domain."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PairingVerifyResponse(BaseModel):
    valid: bool = True


class TossConnectRequest(BaseModel):
    app_key: str = Field(alias="appKey", min_length=1)
    secret_key: str = Field(alias="secretKey", min_length=1)

    model_config = {"populate_by_name": True}


class AccountInfo(BaseModel):
    seq: str
    name: str


class TossConnectResponse(BaseModel):
    connected: bool = True
    account: AccountInfo


class AuthStatusResponse(BaseModel):
    """Launch-gate status: whether a Toss account is connected."""

    connected: bool
