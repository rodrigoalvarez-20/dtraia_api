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
from dtraia_llm.models.llama2 import Llama2

global llm_pipeline, vector_storage
global llama_model


@asynccontextmanager
def lifespan(app: FastAPI):
    # Load the ML model
    global llama_model
    llama_model = Llama2()
    yield
    # Clean up the ML models and release the resources

async def load_llama():
    print("Loading LLAMA....")

chat_app = FastAPI(lifespan=lifespan, on_startup=[load_llama])


