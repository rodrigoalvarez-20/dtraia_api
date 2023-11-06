from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from datetime import datetime
from uuid import uuid4
import json

## Custom imports
from dtraia_api.models.users import LoginUserModel, RegisterUserModel
from dtraia_api.utils.decorators import dtraia_decorator
from dtraia_api.utils.auth import generate_login_token, validate_request


users_router = APIRouter(prefix="/users")


@users_router.post("/register")
@dtraia_decorator("users", "users")
def register_user(user_data: RegisterUserModel, log = None, db = None):
    log.debug("Iniciando registro del usuario: {}".format(user_data.email))
    
    if db.find_one({ "email": user_data.email }):
        log.error("El usuario {} ya se encuentra registrado".format(user_data.email))
        return JSONResponse(
            status_code=400,
            content={
                "error": "El usuario ya se encuentra registrado"
            }
        )
    
    created_user_json = json.loads(user_data.json())
    
    created_user_json["createdDate"] = datetime.now().isoformat()
    created_user_json["chatsId"] = []
    created_user_json["gns3_projects"] = []
    created_user_json["profilePic"] = "default.png"
    
    try:
        inserted_user = db.insert_one(created_user_json)
        
        if not inserted_user.inserted_id:
            raise Exception("Usuario no insertado")

        log.info("Se ha registrado correctamente el usuario: {}".format(user_data.email))
        
        # Generar token
        login_token = generate_login_token(str(inserted_user.inserted_id), user_data.email)
        # Regresar info + Token
        del created_user_json["_id"]
        del created_user_json["password"]
        created_user_json["token"] = login_token
        return JSONResponse(
            status_code=201,
            content={
                "message": "Se ha registrado correctamente el usuario",
                "user": created_user_json
            }
        )
        
    except Exception as ex:
        log.error("Ha ocurrido un error al tratar de registrar el usuario: {} - {}".format(user_data.email, str(ex)))
        return JSONResponse(
            status_code=500,
            content={
                "error": "Ha ocurrido un error al registrar el usuario, por favor intente de nuevo."
            }
        )


@users_router.post("/login")
@dtraia_decorator("users", "users")
def login_user(user_data: LoginUserModel, log = None, db = None):
    log.debug("Iniciando login del usuario: {}".format(user_data.email))
    
    user_in_db = db.find_one({ "email": user_data.email })
    
    if not user_in_db:
        log.error("El usuario {} no se encuentra registrado".format(user_data.email))
        return JSONResponse(
            status_code=404,
            content={
                "error": "El usuario no se encuentra registrado"
            }
        )

    if user_data.password != user_in_db["password"]:
        log.error("Las contraseñas no coinciden. Usuario {}".format(user_data.email))
        return JSONResponse(
            status_code=400,
            content={
                "error": "Las credenciales son incorrectas"
            }
        )
        
    log.info("Inicio de sesion correcto del usuario: {}".format(user_data.email))
        
    # Generar token
    login_token = generate_login_token(str(user_in_db["_id"]), user_data.email)
    # Regresar info + Token
    del user_in_db["_id"]
    del user_in_db["password"]
    user_in_db["token"] = login_token
    return JSONResponse(
        status_code=200,
        content={
            "message": "Inicio de sesion correcto",
            "user": user_in_db
        }
    )


@users_router.get("/profile")
@dtraia_decorator("users", "users")
def get_user_profile(request: Request, log = None, db = None):
    request_status = validate_request(request)
    if request_status["status"] != 200:
        return JSONResponse(status_code=request_status["status"], content={"error": request_status["error"]})

    user_email = request_status["email"]
    user_info = db.find_one({ "email": user_email }, { "_id": 0, "password": 0 })
    if not user_info:
        log.info("Error al recuperar la informacion del usuario {}. El usuario no existe".format(user_email))
        return JSONResponse(
            status_code=400,
            content={
                "error": "Ha ocurrido un error al recuperar el perfil del usuario"
            }
        )
    

    return JSONResponse(status_code=200, content=user_info)

    
@users_router.get("/chat_history")
@dtraia_decorator("api","chat",True)
def get_user_chats(chat_id: str, request: Request, log = None, db = None):
    request_status = validate_request(request)
    if request_status["status"] != 200:
        return JSONResponse(status_code=request_status["status"], content={"error": request_status["error"]})

    user_email = request_status["email"]
    
    ## TODO Refactorizar esto, moviendo las consultas a business
    
    user_info = db["users"].find_one({ "email": user_email })
    if not user_info:
        log.info("Error al recuperar la informacion del chat {} del usuario {}. El usuario no existe".format(chat_id, user_email))
        return JSONResponse(
            status_code=400,
            content={
                "error": "Ha ocurrido un error al recuperar el perfil del usuario"
            }
        )
    
    user_chats = user_info["chatsId"]

    #print(user_chats)

    #list_of_ids = [ x["chat_id"] for x in user_chats ]
    
    if not chat_id in user_chats:
        log.warning("El chat {} no se encuentra en el perfil del usuario {}".format(chat_id, user_email))
        return JSONResponse(
            status_code=404,
            content={
                "error": "No se ha encontrado el chat indicado en el perfil del usuario"
            }
        )
        
    
    chat_messages = list(db["conversations"].find({ "chat_id": chat_id }, { "_id": 0 }))
    
    fmt_messages = []

    for m in chat_messages:
        json_msg = json.loads(m["message_info"])
        #message_data = json_msg["data"]
        fmt_messages.append({
            "type": json_msg["type"],
            "message": json_msg["data"]["content"],
            "datetime": json_msg["createdAt"]
        })

    log.debug("Total de mensajes recuperados: {} - SessionID: {} ".format(len(fmt_messages), chat_id))
    
    return JSONResponse(
        status_code=200,
        content={
            "messages": fmt_messages
        }
    )


@users_router.post("/new_chat")
@dtraia_decorator("api", "users")
def create_new_chat_for_user(request: Request, log = None, db = None):
    request_status = validate_request(request)
    if request_status["status"] != 200:
        return JSONResponse(status_code=request_status["status"], content={"error": request_status["error"]})

    user_email = request_status["email"]
    
    user_info = db.find_one({ "email": user_email })
    if not user_info:
        log.info("Error al crear un nuevo chat para el usuario {}. El usuario no existe".format(user_email))
        return JSONResponse(
            status_code=400,
            content={
                "error": "Ha ocurrido un error al recuperar el perfil del usuario"
            }
        )
    
    new_chat_id = "".join(str(uuid4().hex).split("-"))[:15]
    actual_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    db.update_one({ "email": user_email }, { "$push": { "chatsId": { "datetime": actual_time , "name": new_chat_id, "chat_id": new_chat_id } } })
    log.debug("Chat con el ID {} creado para el usuario {}".format(new_chat_id, user_email))
    
    return JSONResponse(
        status_code=201,
        content={
            "message": "Se ha creado correctamente el chat",
            "chat_id": new_chat_id
        }
    )