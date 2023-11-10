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
from dtraia_llm.main import build_llm_pipeline, build_llm_w_memory
from dtraia_llm.utils.agent_memory import print_agent_memory

global convo_pipeline
global convo_tools

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    global convo_pipeline
    global convo_tools
    convo_pipeline, convo_tools = build_llm_pipeline(model_name="local_llama2_chat_13b_ft")
    yield
    del convo_pipeline
    del convo_tools
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
@app.post("/api/chat/{chat_id}")
@dtraia_decorator("api", "chat", True)
def chat_with_ia(chat_id: str, user_message: MessageChat, request: Request, use_mongo: bool = True, log = None, db = None):
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

    user_chats = user_info["chatsId"]

    list_of_ids = [ x["chat_id"] for x in user_chats ]
    
    if not chat_id in list_of_ids:
        log.warning("El chat {} no se encuentra en el perfil del usuario {}".format(chat_id, user_email))
        return JSONResponse(
            status_code=404,
            content={
                "error": "No se ha encontrado el chat indicado en el perfil del usuario"
            }
        )

    global convo_pipeline
    global convo_tools

    convo_agent = build_llm_w_memory(convo_pipeline, convo_tools, chat_id)

    print(convo_agent.memory.chat_memory.messages)

    convo_response = convo_agent(user_message.question)

    return JSONResponse(status_code=200, content={
        "message": convo_response["output"]
    })

if __name__ == "__main__":
    PORT = os.environ["PORT"] if "PORT" in os.environ else "5000"
    uvicorn.run(app, host="0.0.0.0", port=PORT)
    