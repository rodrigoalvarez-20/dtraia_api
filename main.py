from fastapi import FastAPI, WebSocket, WebSocketException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import os

### Custom imports

from dtraia_api.routes.users import users_router
from dtraia_api.routes.chat import chat_app
from dtraia_api.utils.auth import validate_request, auth
from dtraia_api.utils.decorators import dtraia_decorator

# LLM
from dtraia_llm.models.llama2 import Llama2

global llama_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    global llama_model
    llama_model = Llama2()
    yield
    # Clean up the ML models and release the resources


app = FastAPI(
    title="DTRAIA API service",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#app.add_websocket_route("/api/chat", chat_websocket)
app.include_router(router=users_router, prefix="/api")
#app.mount("/api", chat_app)

@app.get("/api")
def start_route():
    
    return JSONResponse(
        status_code=200,
        content={
            "message": "Ok"
        }
    )

### Websocket Route

@app.websocket("/api/chat")
@dtraia_decorator("api", "users", True)
async def chat_with_ia(
    websocket: WebSocket,
    chat_id: str,
    token: str, log = None, db = None):
    
    await websocket.accept()
    
    auth_resp = auth(token)
    
    # Validar sesion
    if auth_resp["status"] != 200:
        await websocket.send_json({
            "status": auth_resp["status"],
            "error": auth_resp["error"]
        })
        raise WebSocketException(status.WS_1007_INVALID_FRAME_PAYLOAD_DATA, auth_resp["error"])
    
    # Validar el ID del chat
    user_email = auth_resp["email"]
    
    user_info = db["users"].find_one({ "email": user_email })
    
    if not user_info:
        await websocket.send_json({
            "status": 404,
            "error": "El usuario no se encuentra registrado"
        })
    
    while True:
        data = await websocket.receive_text()
        response = llama_model.generate(
            data, 
            temperature=0.2, 
            top_k=10, 
            top_p=0.75,
            max_new_tokens=128
            #num_beams=0
            #repetition_penalty=1.5
        )
        await websocket.send_text(response)




if __name__ == "__main__":
    PORT = os.environ["PORT"] if "PORT" in os.environ else "5000"
    uvicorn.run(app, host="0.0.0.0", port=PORT)
    