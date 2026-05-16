from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse

from connectors.base import OAuthSessionData
from connectors.registry import get_connector
from connectors.session_store import SESSION_TTL_SECONDS, STORE

HOST = "0.0.0.0"
PORT = 8088


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        return

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _parse_form(self) -> dict[str, str]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        form = parse_qs(raw)
        return {k: (v[0].strip() if v else "") for k, v in form.items()}

    def _parse_oauth_route(self) -> tuple[str | None, str | None]:
        path = urlparse(self.path).path
        parts = [part for part in path.split("/") if part]
        if len(parts) != 3 or parts[0] != "oauth":
            return None, None
        return parts[1], parts[2]

    def do_POST(self) -> None:  # noqa: N802
        connector_id, action = self._parse_oauth_route()
        if not connector_id or not action:
            self._json(404, {"error": "not_found"})
            return
        connector = get_connector(connector_id)
        if not connector:
            self._json(404, {"error": "connector_not_found", "detail": f"Unsupported connector: {connector_id}"})
            return

        if action == "session":
            self._handle_oauth_session_create(connector_id, connector)
            return
        if action == "exchange":
            self._handle_oauth_exchange(connector_id, connector)
            return
        if action == "token":
            # Backward compatibility endpoint alias for old frontend flow.
            self._handle_legacy_x_token(connector_id, connector)
            return
        self._json(404, {"error": "not_found", "detail": f"Unsupported action: {action}"})

    def do_GET(self) -> None:  # noqa: N802
        connector_id, action = self._parse_oauth_route()
        if not connector_id or not action:
            self._json(404, {"error": "not_found"})
            return
        connector = get_connector(connector_id)
        if not connector:
            self._json(404, {"error": "connector_not_found", "detail": f"Unsupported connector: {connector_id}"})
            return

        if action not in {"users-me", "verify"}:
            self._json(404, {"error": "not_found", "detail": f"Unsupported action: {action}"})
            return

        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            self._json(400, {"error": "invalid_request", "detail": "Missing Bearer token."})
            return

        access_token = auth.removeprefix("Bearer ").strip()
        try:
            payload = connector.verify_access_token(access_token)
            self._json(200, payload)
        except HTTPError as err:
            self._handle_http_error(err)
        except Exception as err:  # noqa: BLE001
            self._json(502, {"error": "upstream_error", "detail": str(err)})

    def _handle_http_error(self, err: HTTPError) -> None:
        try:
            body = err.read().decode("utf-8")
            payload = json.loads(body)
        except Exception:
            payload = {"error": "upstream_error", "detail": str(err)}
        self._json(err.code, payload)

    def _handle_oauth_session_create(self, connector_id: str, connector) -> None:
        form = self._parse_form()

        client_id = form.get("client_id", "")
        client_secret = form.get("client_secret", "")
        redirect_uri = form.get("redirect_uri", "")
        scope = form.get("scope", "users.read tweet.read")

        if not client_id or not redirect_uri:
            self._json(400, {"error": "invalid_request", "detail": "Missing client_id or redirect_uri."})
            return

        session_data = connector.new_session_data(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
        )
        session_id = STORE.create(
            connector_id,
            {
                "state": session_data.state,
                "verifier": session_data.verifier,
                "client_id": session_data.client_id,
                "client_secret": session_data.client_secret,
                "redirect_uri": session_data.redirect_uri,
                "scope": session_data.scope,
            },
        )

        authorize_url = connector.build_authorize_url(session_data)

        self._json(
            200,
            {
                "session_id": session_id,
                "authorize_url": authorize_url,
                "expires_in": SESSION_TTL_SECONDS,
            },
        )

    def _handle_oauth_exchange(self, connector_id: str, connector) -> None:
        form = self._parse_form()

        session_id = form.get("session_id", "")
        code = form.get("code", "")
        state = form.get("state", "")

        if not session_id or not code or not state:
            self._json(400, {"error": "invalid_request", "detail": "Missing session_id, code, or state."})
            return

        session = STORE.get(session_id)
        if not session:
            self._json(400, {"error": "invalid_session", "detail": "OAuth session not found or expired."})
            return
        if session.connector_id != connector_id:
            self._json(400, {"error": "invalid_session", "detail": "Connector mismatch for session."})
            return

        expected_state = str(session.payload.get("state", ""))
        if state != expected_state:
            self._json(400, {"error": "invalid_state", "detail": "OAuth state mismatch."})
            return

        payload = session.payload
        session_data = OAuthSessionData(
            state=str(payload.get("state", "")),
            verifier=str(payload.get("verifier", "")),
            client_id=str(payload.get("client_id", "")),
            client_secret=str(payload.get("client_secret", "")),
            redirect_uri=str(payload.get("redirect_uri", "")),
            scope=str(payload.get("scope", "")),
        )

        try:
            token_payload = connector.exchange_code(session_data, code)
            self._json(200, token_payload)
            STORE.pop(session_id)
        except HTTPError as err:
            self._handle_http_error(err)
        except NotImplementedError as err:
            self._json(501, {"error": "not_implemented", "detail": str(err)})
        except Exception as err:  # noqa: BLE001
            self._json(502, {"error": "upstream_error", "detail": str(err)})

    def _handle_legacy_x_token(self, connector_id: str, connector) -> None:
        # Backward compatibility for old clients posting direct code/verifier/secret.
        form = self._parse_form()
        code = form.get("code", "")
        verifier = form.get("code_verifier", "")
        client_id = form.get("client_id", "")
        client_secret = form.get("client_secret", "")
        redirect_uri = form.get("redirect_uri", "")

        if not code or not verifier or not client_id or not redirect_uri:
            self._json(400, {"error": "invalid_request", "detail": "Missing required fields."})
            return

        session_data = OAuthSessionData(
            state="",
            verifier=verifier,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=form.get("scope", ""),
        )
        try:
            token_payload = connector.exchange_code(session_data, code)
            self._json(200, token_payload)
        except HTTPError as err:
            self._handle_http_error(err)
        except Exception as err:  # noqa: BLE001
            self._json(502, {"error": "upstream_error", "detail": str(err)})


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), Handler)
    server.serve_forever()
