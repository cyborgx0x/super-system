from __future__ import annotations

import base64
import secrets
import time
from dataclasses import dataclass

SESSION_TTL_SECONDS = 10 * 60


@dataclass(slots=True)
class SessionRecord:
    connector_id: str
    created_at: float
    payload: dict[str, str]


class SessionStore:
    def __init__(self, ttl_seconds: int = SESSION_TTL_SECONDS) -> None:
        self._ttl = ttl_seconds
        self._sessions: dict[str, SessionRecord] = {}

    @staticmethod
    def _new_id() -> str:
        return base64.urlsafe_b64encode(secrets.token_bytes(18)).decode("utf-8").rstrip("=")

    def cleanup(self) -> None:
        now = time.time()
        expired_ids = [sid for sid, rec in self._sessions.items() if now - rec.created_at > self._ttl]
        for sid in expired_ids:
            self._sessions.pop(sid, None)

    def create(self, connector_id: str, payload: dict[str, str]) -> str:
        self.cleanup()
        session_id = self._new_id()
        self._sessions[session_id] = SessionRecord(
            connector_id=connector_id,
            created_at=time.time(),
            payload=payload,
        )
        return session_id

    def get(self, session_id: str) -> SessionRecord | None:
        self.cleanup()
        return self._sessions.get(session_id)

    def pop(self, session_id: str) -> SessionRecord | None:
        self.cleanup()
        return self._sessions.pop(session_id, None)

    def pop_by_state(self, connector_id: str, state: str) -> SessionRecord | None:
        self.cleanup()
        for sid, rec in list(self._sessions.items()):
            if rec.connector_id == connector_id and rec.payload.get("state") == state:
                return self._sessions.pop(sid)
        return None


STORE = SessionStore()
