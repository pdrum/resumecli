import os
from contextlib import contextmanager
from typing import Any, Awaitable, Callable
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from starlette.testclient import WebSocketTestSession

from src.renderer import ResumeTemplate
from src.server import (
    ENV_KEY_RESUME_SOURCE_FILE,
    ENV_KEY_RESUME_TEMPLATE_NAME,
    PING_MESSAGE,
    app,
    get_resume_service,
    html,
)
from src.service import ResumeService


@pytest.fixture
def mock_resume_service() -> ResumeService:
    mock_service = MagicMock(spec=ResumeService)
    mock_service.watch_file = AsyncMock()
    return mock_service


@contextmanager
def inject_mock_service(mock_service: ResumeService) -> Any:
    original_override = app.dependency_overrides.get(get_resume_service)
    app.dependency_overrides[get_resume_service] = lambda: mock_service
    try:
        yield
    finally:
        if original_override:
            app.dependency_overrides[get_resume_service] = original_override
        else:
            app.dependency_overrides.pop(get_resume_service, None)


@pytest.mark.asyncio
async def test_sending_previews_on_websocket(mock_resume_service: ResumeService) -> None:
    test_message = "<html><body>Test message from mock service</body></html>"
    test_file_path = "some/file.yaml"

    async def fake_show_previews(on_preview_updated: Callable[[str], Awaitable[None]], *args, **kwargs) -> None:
        await on_preview_updated(test_message)
        await on_preview_updated(test_message)
        return

    mock_resume_service.show_previews.side_effect = fake_show_previews

    with inject_mock_service(mock_resume_service):
        os.environ[ENV_KEY_RESUME_SOURCE_FILE] = test_file_path
        os.environ[ENV_KEY_RESUME_TEMPLATE_NAME] = ResumeTemplate.MINIMAL_BLUE.value

        with TestClient(app).websocket_connect("/ws") as ws:
            for _ in range(2):
                received_message = listen_ignoring_pings(ws)
                assert received_message == test_message
            ws.close()

    mock_resume_service.show_previews.assert_called_once()


@pytest.mark.asyncio
async def test_sending_ping_messages(mock_resume_service: ResumeService) -> None:
    test_file_path = "some/file.yaml"

    async def fake_show_previews(*args, **kwargs) -> None:
        pass

    mock_resume_service.show_previews.side_effect = fake_show_previews

    with inject_mock_service(mock_resume_service):
        os.environ[ENV_KEY_RESUME_SOURCE_FILE] = test_file_path
        os.environ[ENV_KEY_RESUME_TEMPLATE_NAME] = ResumeTemplate.MINIMAL_BLUE.value

        with TestClient(app).websocket_connect("/ws") as ws:
            for _ in range(2):
                assert ws.receive_text() == PING_MESSAGE
                ws.send_text("pong")
            ws.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "env_vars",
    [
        {ENV_KEY_RESUME_TEMPLATE_NAME: ResumeTemplate.MINIMAL_BLUE.value},
        {ENV_KEY_RESUME_SOURCE_FILE: "some/file.yaml"},
    ],
)
async def test_websocket_missing_env_var(mock_resume_service: ResumeService, env_vars: dict) -> None:
    with inject_mock_service(mock_resume_service):
        with pytest.raises(KeyError):
            with patch.dict(os.environ, env_vars, clear=True):
                with TestClient(app).websocket_connect("/ws") as websocket:
                    websocket.receive_text()


@pytest.mark.asyncio
async def test_get_endpoint_returns_html() -> None:
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert response.text == html


def listen_ignoring_pings(ws: WebSocketTestSession) -> str:
    while True:
        message = ws.receive_text()
        if message == "ping":
            ws.send_text("pong")
            continue
        return message
