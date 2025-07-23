from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import random
import asyncio

app = FastAPI()

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
        number = random.randint(1, 100)
        await websocket.send_text(str(number))
        await asyncio.sleep(1)
