from __future__ import annotations

from .buffer_connector import CONNECTOR as BUFFER_CONNECTOR
from .x_connector import CONNECTOR as X_CONNECTOR

CONNECTOR_REGISTRY = {
    X_CONNECTOR.connector_id: X_CONNECTOR,
    BUFFER_CONNECTOR.connector_id: BUFFER_CONNECTOR,
}


def get_connector(connector_id: str):
    return CONNECTOR_REGISTRY.get(connector_id)
