from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class OAuthSessionInput:
    client_id: str
    client_secret: str
    redirect_uri: str
    scope: str


@dataclass(slots=True)
class OAuthSessionData:
    state: str
    verifier: str
    client_id: str
    client_secret: str
    redirect_uri: str
    scope: str


class OAuthConnector(Protocol):
    connector_id: str

    def build_authorize_url(self, data: OAuthSessionData) -> str:
        ...

    def exchange_code(self, data: OAuthSessionData, code: str) -> dict:
        ...

    def verify_access_token(self, access_token: str) -> dict:
        ...
