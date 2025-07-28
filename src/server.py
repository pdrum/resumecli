import os

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

from renderer import ResumeRenderer, ResumeTemplate
from service import ResumeService

app = FastAPI()

ENV_KEY_RESUME_SOURCE_FILE = "RESUME_SOURCE_FILE"

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Random Number Stream</title>
        <script>
            let ws;
            function connect() {
                ws = new WebSocket(`ws://${location.host}/ws`);
                ws.onmessage = function(event) {
                    document.body.innerHTML = event.data;
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


@app.get("/", response_class=HTMLResponse)
async def get() -> str:
    return html


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    while True:
        service = ResumeService(renderer=ResumeRenderer())
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
