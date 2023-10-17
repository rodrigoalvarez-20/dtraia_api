from fastapi import FastAPI, Request#, WebSocket, WebSocketException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import os
import torch

### Custom imports

from dtraia_api.routes.users import users_router
#from dtraia_api.routes.chat import chat_app
from dtraia_api.utils.auth import validate_request, auth
from dtraia_api.utils.decorators import dtraia_decorator
from dtraia_api.models.chats import MessageChat

# LLM
from dtraia_llm.models.llama2 import Llama2

global llama_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    global llama_model
    llama_model = Llama2(
        model_name="local", 
        quant=True,
        _4bits=True,
        double_quant=True
    )
    yield
    del llama_model
    torch.cuda.empty_cache()
    #sync; echo 1 > /proc/sys/vm/drop_caches
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

### Chat Route
@app.post("/api/message/{chat_id}")
@dtraia_decorator("api", "chat", True)
def chat_with_ia(chat_id: str, version: str, user_message: MessageChat, request: Request, use_mongo: bool = True, log = None, db = None):
    request_status = validate_request(request)
    if request_status["status"] != 200:
        return JSONResponse(status_code=request_status["status"], content={"error": request_status["error"]})

    user_email = request_status["email"]
    
    user_info = db["users"].find_one({ "email": user_email })
    if not user_info:
        log.info("Error al agregar un mensaje al chat para el usuario {}. El usuario no existe".format(user_email))
        return JSONResponse(
            status_code=400,
            content={
                "error": "Ha ocurrido un error al recuperar el perfil del usuario"
            }
        )

    #user_chats = user_info["chatsId"]
    
    #if not chat_id in user_chats:
    #    log.warning("El chat {} no se encuentra en el perfil del usuario {}".format(chat_id, user_email))
    #    return JSONResponse(
    #        status_code=404,
    #        content={
    #            "error": "No se ha encontrado el chat indicado en el perfil del usuario"
    #        }
    #    )

    if version == "v1":
        llm_response = llama_model.generate(user_message.question)
    else:
        llm_response = llama_model.pipeline_generate(user_message.question)

    return JSONResponse(status_code=200, content={
        "message": llm_response
    })


if __name__ == "__main__":
    PORT = os.environ["PORT"] if "PORT" in os.environ else "5000"
    uvicorn.run(app, host="0.0.0.0", port=PORT)
    