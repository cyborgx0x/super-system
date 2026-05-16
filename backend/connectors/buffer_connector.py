from __future__ import annotations


class BufferOAuthConnector:
    connector_id = "buffer"

    def new_session_data(self, client_id: str, client_secret: str, redirect_uri: str, scope: str):
        raise NotImplementedError("Buffer connector will be implemented in next step.")

    def build_authorize_url(self, data):
        raise NotImplementedError("Buffer connector will be implemented in next step.")

    def exchange_code(self, data, code: str):
        raise NotImplementedError("Buffer connector will be implemented in next step.")

    def verify_access_token(self, access_token: str):
        raise NotImplementedError("Buffer connector will be implemented in next step.")


CONNECTOR = BufferOAuthConnector()
