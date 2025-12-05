from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/")
async def get():
    return HTMLResponse("""
        <html>
            <body>
                <h1>WebSocket Test</h1>
                <script>
                    let ws = new WebSocket("ws://localhost:8000/ws");
                    ws.onmessage = (event) => {
                        let log = document.getElementById('log');
                        log.innerText += event.data + '\\n';
                    };
                    function sendMsg() {
                        let input = document.getElementById('input');
                        ws.send(input.value);
                        input.value = '';
                    }
                </script>
                <input id="input" type="text" /><button onclick="sendMsg()">Send</button>
                <pre id="log"></pre>
            </body>
        </html>
    """)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Here you can parse data as JSON, handle events, etc.
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        pass  # Client disconnected

