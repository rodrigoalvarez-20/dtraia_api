from fastapi import FastAPI, Request#, WebSocket, WebSocketException, status
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import os
import torch

### Custom imports

from dtraia_api.routes.users import users_router
from dtraia_api.routes.rate_message import rates_router

from dtraia_api.utils.auth import validate_request, auth
from dtraia_api.utils.decorators import dtraia_decorator
from dtraia_api.models.chats import MessageChat

# LLM
#from dtraia_llm.main import load_pipeline, create_conversational_agent, create_agent_executor
#from dtraia_llm.memory.llm_memory import build_memory
#from dtraia_llm.utils.agent_memory import print_agent_memory
from dtraia_llm.main import manual_conversation
from dtraia_llm.models.llama2 import Llama2
from dtraia_llm.models.lamini_flan import LaminiT5

global llama_2
global convo_agent
global lamini_t5

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    global llama_2
    global lamini_t5
    #llama_2 = Llama2(quant=True, _4bits=True, double_quant=False, device_map={"": 1})
    #lamini_t5 = LaminiT5(device_map={ "": 1})
    yield
    del llama_2
    torch.cuda.empty_cache()
    #sync; echo 1 > /proc/sys/vm/drop_caches
    #sudo swapoff -a; sudo swapon -a
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
app.include_router(router=rates_router, prefix="/api")
#app.mount("/api", chat_app)

@app.get("/api")
def start_route():
    
    return JSONResponse(
        status_code=200,
        content={
            "message": "Ok"
        }
    )

@app.options("*")
def cors_handle():
    print("Options requested")
    response_headers = {"Access-Control-Allow-Origin": "*"}
    return JSONResponse(status_code=200,
        content={},
        headers=response_headers)

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
    
    if chat_id not in list_of_ids:
        log.warning("El chat {} no se encuentra en el perfil del usuario {}".format(chat_id, user_email))
        return JSONResponse(
            status_code=404,
            content={
                "error": "No se ha encontrado el chat indicado en el perfil del usuario"
            }
        )

    global llama_2
    global lamini_t5

    try:
        ai_response = manual_conversation(llama_2, chat_id, user_message.question)
    except Exception as omex:
        print(omex)
        ai_response = manual_conversation(llama_2, chat_id, user_message.question)
    finally:
        torch.cuda.empty_cache()    
    
    question_topic : str = lamini_t5.process_text(user_message.question)

    question_topic = question_topic.replace("\"", "")

    db["users"].update_one({ "email": user_email, "chatsId.chat_id": chat_id }, { "$set": { "chatsId.$.name": question_topic } }, False)

    return JSONResponse(status_code=200, content={
        "message": ai_response,
        "topic": question_topic
    })

if __name__ == "__main__":
    PORT = os.environ["PORT"] if "PORT" in os.environ else 5000
    uvicorn.run(app, host="0.0.0.0", port=PORT)
    