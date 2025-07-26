import os

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

from preview import PreviewService
from renderer import Template, ResumeRenderer

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
async def get():
    return html

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        preview_service = PreviewService(renderer=ResumeRenderer())
        await preview_service.watch_file(
            file_path=os.environ.get(ENV_KEY_RESUME_SOURCE_FILE), # TODO: handle errors and null
            on_preview_updated=lambda content: websocket.send_text(content),
            template=Template.DEFAULT_RESUME
        )
