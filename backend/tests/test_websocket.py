"""Integration test for the WebSocket endpoint."""

from fastapi.testclient import TestClient

from proof_editor.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_websocket_connects() -> None:
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        # Send a task.select message
        ws.send_json({"type": "task.select", "task_type": "essay", "topic": "test"})
        # Should get a status message back (or LLM error since no API key)
        response = ws.receive_json()
        assert response["type"] in ("status", "error", "thought")


def test_websocket_unknown_message_type() -> None:
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"type": "unknown.type"})
        response = ws.receive_json()
        assert response["type"] == "error"
        assert "Unknown message type" in response["message"]


def test_websocket_invalid_json() -> None:
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        ws.send_text("not valid json{{{")
        response = ws.receive_json()
        assert response["type"] == "error"
        assert "Invalid JSON" in response["message"]
