"""Integration test for the WebSocket endpoint."""

import os

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from proof_editor.main import app

WS_HEADERS = {"origin": "http://localhost:5173"}

# Ensure a JWT secret is set for tests
os.environ.setdefault(
    "JWT_SECRET_KEY", "test-secret-key-that-is-at-least-32-characters-long"
)


def _get_auth_cookie(client: TestClient) -> str:
    """Register a test user and return the access_token cookie value."""
    res = client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword123",
            "name": "Test User",
        },
    )
    if res.status_code == 409:
        # User already exists, log in instead
        res = client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"},
        )
    assert res.status_code == 200
    return res.json()["token"]


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_websocket_connects() -> None:
    client = TestClient(app)
    token = _get_auth_cookie(client)
    client.cookies.set("access_token", token)
    with client.websocket_connect("/ws", headers=WS_HEADERS) as ws:
        # Send a task.select message
        ws.send_json({"type": "task.select", "task_type": "essay", "topic": "test"})
        # Should get a status message back (or LLM error since no API key)
        response = ws.receive_json()
        assert response["type"] in ("status", "error", "thought")


def test_websocket_unknown_message_type() -> None:
    client = TestClient(app)
    token = _get_auth_cookie(client)
    client.cookies.set("access_token", token)
    with client.websocket_connect("/ws", headers=WS_HEADERS) as ws:
        ws.send_json({"type": "unknown.type"})
        response = ws.receive_json()
        assert response["type"] == "error"
        assert "Unknown message type" in response["message"]


def test_websocket_invalid_json() -> None:
    client = TestClient(app)
    token = _get_auth_cookie(client)
    client.cookies.set("access_token", token)
    with client.websocket_connect("/ws", headers=WS_HEADERS) as ws:
        ws.send_text("not valid json{{{")
        response = ws.receive_json()
        assert response["type"] == "error"
        assert "Invalid JSON" in response["message"]


def test_websocket_rejects_bad_origin() -> None:
    """Connection from disallowed origin should be rejected."""
    client = TestClient(app)
    token = _get_auth_cookie(client)
    client.cookies.set("access_token", token)
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws", headers={"origin": "http://evil.com"}):
            pass


def test_websocket_rejects_no_auth() -> None:
    """Connection without auth should be rejected with 4001."""
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws", headers=WS_HEADERS):
            pass
