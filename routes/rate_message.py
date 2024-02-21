from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from pymongo import ReturnDocument
from datetime import datetime
from uuid import uuid4
import json
from bson.objectid import ObjectId

## Custom imports
from dtraia_api.models.rate import RateMessage
from dtraia_api.utils.decorators import dtraia_decorator
from dtraia_api.utils.auth import validate_request
#from dtraia_api.utils.common import dec_rsa_front

rates_router = APIRouter(prefix="/rate_message")



@rates_router.post("/rate")
@dtraia_decorator("chat", "users", True)
def rate_message(rating_message: RateMessage, request: Request, log = None, db = None):
    request_status = validate_request(request)
    if request_status["status"] != 200:
        return JSONResponse(status_code=request_status["status"], content={"error": request_status["error"]})

    question_message = db["conversations"].find_one({ "_id": ObjectId(rating_message.qmessage_id) })
    answer_message = db["conversations"].find_one({ "_id": ObjectId(rating_message.amessage_id) })
    
    if not question_message or not answer_message:
        return JSONResponse(status_code=404, content={ "error": "No se han encontrado los mensajes especificados" })
    
    question_message = json.loads(question_message["message_info"])
    answer_message = json.loads(answer_message["message_info"])
    
    feedback_record = {
        "chat_question": question_message["data"]["content"],
        "chat_answer": answer_message["data"]["content"],
        "rate_type": rating_message.rating
    }
    
    inserted_feed = db["feedback"].insert_one(feedback_record)
    
    if not inserted_feed.inserted_id:
        return JSONResponse(status_code=500, content={ "error": "Ha ocurrido un error al agregar los datos a la tabla de Feedback" })
    
    
    updated_answer_message = db["conversations"].find_one_and_update({ "_id": ObjectId(rating_message.amessage_id) }, { "$set": { "rate": rating_message.rating } }, return_document = ReturnDocument.AFTER)
    
    updated_answer_message["_id"] = str(updated_answer_message["_id"])
    
    return JSONResponse(status_code=200, content={"message": "Se ha agregado correctamente al feedback", "update": updated_answer_message })