import asyncio
import os

from fastapi import Depends, FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from starlette.websockets import WebSocketDisconnect

from src.renderer import ResumeRenderer, ResumeTemplate
from src.service import ResumeService

app = FastAPI()

ENV_KEY_RESUME_SOURCE_FILE = "RESUME_SOURCE_FILE"
ENV_KEY_RESUME_TEMPLATE_NAME = "RESUME_TEMPLATE"

PING_MESSAGE = "ping"

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Resume Preview</title>
        <script>
            let ws;
            let reconnectInterval = 1000; // 1 second reconnection interval

            function connect() {
                ws = new WebSocket(`ws://${location.host}/ws`);

                ws.onmessage = function(event) {
                    if (event.data === 'ping') {
                        console.log('Received ping, sending pong');
                        ws.send('pong');
                        return;
                    }
                    document.body.innerHTML = event.data;
                };

                ws.onclose = function() {
                    console.log('WebSocket connection closed. Attempting to reconnect...');
                    setTimeout(connect, reconnectInterval);
                };

                ws.onerror = function(err) {
                    console.error('WebSocket error:', err);
                    ws.close(); // This will trigger onclose event
                };
            }

            window.onload = connect;
        </script>
    </head>
    <body>
        Connecting...
    </body>
</html>
"""


def get_resume_service() -> ResumeService:
    return ResumeService(renderer=ResumeRenderer())


@app.get("/", response_class=HTMLResponse)
async def get() -> str:
    return html


@app.websocket("/ws")
async def live_resume_preview_endpoint(
    websocket: WebSocket,
    service: ResumeService = Depends(get_resume_service),
) -> None:
    await websocket.accept()

    async def send_update(content: str) -> None:
        await websocket.send_text(content)

    preview_showing_task = asyncio.create_task(
        service.show_previews(
            file_path=get_env_or_error(ENV_KEY_RESUME_SOURCE_FILE),
            on_preview_updated=send_update,
            template=ResumeTemplate(get_env_or_error(ENV_KEY_RESUME_TEMPLATE_NAME)),
        )
    )

    try:
        while True:
            await websocket.send_text(PING_MESSAGE)
            await websocket.receive_text()
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        preview_showing_task.cancel()
        return


def get_env_or_error(env_key: str) -> str:
    value = os.environ.get(env_key)
    if not value:
        raise KeyError(f"Environment variable '{env_key}' is not set.")
    return value
