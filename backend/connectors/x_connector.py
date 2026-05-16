from __future__ import annotations

import base64
import hashlib
import json
import secrets
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .base import OAuthSessionData

X_AUTHORIZE_URL = "https://x.com/i/oauth2/authorize"
X_TOKEN_URL = "https://api.x.com/2/oauth2/token"
X_USERS_ME_URL = "https://api.x.com/2/users/me"


def _random_urlsafe(byte_len: int) -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(byte_len)).decode("utf-8").rstrip("=")


def _build_code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


class XOAuthConnector:
    connector_id = "x"

    def new_session_data(self, client_id: str, client_secret: str, redirect_uri: str, scope: str) -> OAuthSessionData:
        return OAuthSessionData(
            state=_random_urlsafe(24),
            verifier=_random_urlsafe(48),
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
        )

    def build_authorize_url(self, data: OAuthSessionData) -> str:
        return X_AUTHORIZE_URL + "?" + urlencode(
            {
                "response_type": "code",
                "client_id": data.client_id,
                "redirect_uri": data.redirect_uri,
                "scope": data.scope,
                "state": data.state,
                "code_challenge": _build_code_challenge(data.verifier),
                "code_challenge_method": "S256",
            }
        )

    def exchange_code(self, data: OAuthSessionData, code: str) -> dict:
        token_body = urlencode(
            {
                "code": code,
                "grant_type": "authorization_code",
                "client_id": data.client_id,
                "redirect_uri": data.redirect_uri,
                "code_verifier": data.verifier,
            }
        ).encode("utf-8")

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        if data.client_secret:
            basic = base64.b64encode(f"{data.client_id}:{data.client_secret}".encode("utf-8")).decode("utf-8")
            headers["Authorization"] = f"Basic {basic}"

        req = Request(X_TOKEN_URL, data=token_body, headers=headers, method="POST")
        with urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def verify_access_token(self, access_token: str) -> dict:
        req = Request(
            X_USERS_ME_URL,
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            method="GET",
        )
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))


CONNECTOR = XOAuthConnector()
