import os

from fastapi import Depends, FastAPI, WebSocket
from fastapi.responses import HTMLResponse

from src.renderer import ResumeRenderer, ResumeTemplate
from src.service import ResumeService

app = FastAPI()

ENV_KEY_RESUME_SOURCE_FILE = "RESUME_SOURCE_FILE"

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
    """Dependency for providing a ResumeService instance."""
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
    while True:
        file_path = os.environ.get(ENV_KEY_RESUME_SOURCE_FILE)
        if not file_path:
            raise ValueError(f"Environment variable '{ENV_KEY_RESUME_SOURCE_FILE}' is not set.")

        async def send_update(content: str) -> None:
            await websocket.send_text(content)

        await service.watch_file(
            file_path=file_path,
            on_preview_updated=send_update,
            template=ResumeTemplate.DEFAULT,
        )
