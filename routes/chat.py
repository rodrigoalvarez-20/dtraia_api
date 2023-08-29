from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, Request, Header, Query, WebSocket, WebSocketException, WebSocketDisconnect, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from typing import Annotated, Union, Optional
from uuid import uuid4


# Custom imports
from dtraia_api.models.chats import MessageChat
from dtraia_api.utils.auth import validate_request, auth
from dtraia_api.utils.decorators import dtraia_decorator
from dtraia_api.utils.mongo import get_mongo_conn_url
## LLM
from dtraia_llm.models.t5_flan import get_flan_model
from dtraia_llm.main import create_llm_pipeline, create_chat_assistant
from dtraia_llm.utils.vector_storage import connect_to_es
from dtraia_llm.embeddings.hf_embeddings import load_embed_model

global llm_pipeline, vector_storage


def on_start():
    model, tokenizer = get_flan_model(model_name="large", quant=False)
    global llm_pipeline
    llm_pipeline = create_llm_pipeline(model, tokenizer)
    emb_model = load_embed_model("mpnet_base")
    global vector_storage
    vector_storage = connect_to_es(emb_model)


chat_websocket = APIRouter(on_startup=[on_start])


@chat_websocket.websocket("/chat")
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
        await websocket.send_text("Data: {} - ChatID: {}".format(data, chat_id))