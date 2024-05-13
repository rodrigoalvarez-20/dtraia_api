from fastapi import APIRouter, Request, Form, UploadFile
from fastapi.responses import JSONResponse
from datetime import datetime
from uuid import uuid4
import json
from bson.objectid import ObjectId
from typing import Optional
import os
## Custom imports
from dtraia_api.models.users import LoginUserModel, RegisterUserModel
from dtraia_api.utils.decorators import dtraia_decorator
from dtraia_api.utils.auth import generate_login_token, validate_request
from dtraia_api.utils.common import dec_rsa_front
from dtraia_api.utils.mailing import send_message

users_router = APIRouter(prefix="/users")


@users_router.post("/register")
@dtraia_decorator("users", "users")
def register_user(user_data: RegisterUserModel, log = None, db = None):
    log.debug("Iniciando registro del usuario: {}".format(user_data.email))

    response_headers = {"Access-Control-Allow-Origin": "*"}
    
    if db.find_one({ "email": user_data.email }):
        log.error("El usuario {} ya se encuentra registrado".format(user_data.email))
        return JSONResponse(
            status_code=400,
            content={
                "error": "El usuario ya se encuentra registrado"
            },
            headers=response_headers
        )
    
    created_user_json = json.loads(user_data.model_dump_json())
    
    created_user_json["createdDate"] = datetime.now().isoformat()
    created_user_json["chatsId"] = []
    created_user_json["gns3_projects"] = []
    created_user_json["profilePic"] = "default.png"
    created_user_json["password"] = dec_rsa_front(created_user_json["password"] )
    
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
            },
            headers=response_headers
        )
        
    except Exception as ex:
        log.error("Ha ocurrido un error al tratar de registrar el usuario: {} - {}".format(user_data.email, str(ex)))
        return JSONResponse(
            status_code=500,
            content={
                "error": "Ha ocurrido un error al registrar el usuario, por favor intente de nuevo."
            },
            headers=response_headers
        )


@users_router.post("/login")
@dtraia_decorator("users", "users")
def login_user(user_data: LoginUserModel, log = None, db = None):
    log.debug("Iniciando login del usuario: {}".format(user_data.email))
    
    user_in_db = db.find_one({ "email": user_data.email })

    #response.headers["Access-Control-Allow-Origin"] = "*"

    response_headers = {"Access-Control-Allow-Origin": "*"}
    
    if not user_in_db:
        log.error("El usuario {} no se encuentra registrado".format(user_data.email))
        return JSONResponse(
            status_code=404,
            content={
                "error": "El usuario no se encuentra registrado"
            },
            headers=response_headers
        )
    
    dec_pwd = dec_rsa_front(user_data.password)

    if dec_pwd != user_in_db["password"]:
        log.error("Las contraseñas no coinciden. Usuario {}".format(user_data.email))
        return JSONResponse(
            status_code=400,
            content={
                "error": "Las credenciales son incorrectas"
            },
            headers=response_headers
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
        },
        headers=response_headers
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
            status_code=404,
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

    list_of_ids = [ x["chat_id"] for x in user_chats ]
    
    if  chat_id not in list_of_ids:
        log.warning("El chat {} no se encuentra en el perfil del usuario {}".format(chat_id, user_email))
        return JSONResponse(
            status_code=404,
            content={
                "error": "No se ha encontrado el chat indicado en el perfil del usuario"
            }
        )
        
    
    chat_messages = list(db["conversations"].find({ "chat_id": chat_id }))
    
    fmt_messages = []

    for m in chat_messages:
        json_msg = json.loads(m["message_info"])
        fmt_messages.append({
            "_id": str(m["_id"]),
            "type": json_msg["type"],
            "message": json_msg["data"]["content"],
            "datetime": json_msg["createdAt"],
            "rate": m["rate"] if "rate" in m else None
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
    chat_inserted = { "datetime": actual_time , "name": new_chat_id, "chat_id": new_chat_id }
    db.update_one({ "email": user_email }, { "$push": { "chatsId": chat_inserted } })
    log.debug("Chat con el ID {} creado para el usuario {}".format(new_chat_id, user_email))
    
    return JSONResponse(
        status_code=201,
        content={
            "message": "Se ha creado correctamente el chat",
            "chat_info": chat_inserted
        }
    )


@users_router.post("/delete_chat")
@dtraia_decorator("api", "users", True)
def delete_user_chat(chat_id: str, request: Request, log = None, db = None):
    request_status = validate_request(request)
    if request_status["status"] != 200:
        return JSONResponse(status_code=request_status["status"], content={"error": request_status["error"]})

    user_email = request_status["email"]
    
    user_info = db["users"].find_one({ "email": user_email })
    if not user_info:
        log.info("Error al eliminar el chat del usuario {}. El usuario no existe".format(user_email))
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

    conv_resp = db["conversations"].delete_many({ "chat_id": chat_id })

    log.info("Se han eliminado {} chats de la tabla de conversaciones".format(conv_resp.deleted_count))

    db["users"].update_one({ "email": user_email }, { "$pull": { "chatsId": { "chat_id": chat_id  } } }, False)
    
    log.info("Se ha eliminado el chat del perfil del usuario")
    
    return JSONResponse(
        status_code=200,
        content={
            "message": "Se ha eliminado correctamente el chat"
        }
    )
    
    
@users_router.post("/recover_password")
@dtraia_decorator("api", "users")
def recover_password(user_data: LoginUserModel, request: Request, log = None, db=None):
    
    user_info = db.find_one({ "email": user_data.email }, { "password": 0 })
    if not user_info:
        log.info("Error al recuperar la informacion del usuario {}. El usuario no existe".format(user_data.email))
        return JSONResponse(
            status_code=404,
            content={
                "error": "Ha ocurrido un error al recuperar el perfil del usuario. El usuario no existe"
            }
        )
    
    recover_token = generate_login_token(str(user_info["_id"]), user_info["email"])
    
    print(recover_token)
    
    fmt_url = "http://localhost:5173/recover_password?token={}".format(recover_token)
    
    
    send_message(user_info["email"], template_params={"username": user_info["nombre"], "email": user_info["email"], "restore_url": fmt_url})
    
    
    return JSONResponse(status_code=200, content={ "message": "Se ha enviado el correo de restauración" })
    
@users_router.post("/reset_password")
@dtraia_decorator("api", "users")
def reset_user_password(user_data: LoginUserModel, request: Request, log = None, db = None):
    request_status = validate_request(request)
    if request_status["status"] != 200:
        return JSONResponse(status_code=request_status["status"], content={"error": request_status["error"]})
    response_headers = {"Access-Control-Allow-Origin": "*"}
    user_email = request_status["email"]
    user_info = db.find_one({ "email": user_email }, { "_id": 0, "password": 0 })
    if not user_info:
        log.info("Error al recuperar la informacion del usuario {}. El usuario no existe".format(user_email))
        return JSONResponse(
            status_code=404,
            content={
                "error": "Ha ocurrido un error al recuperar el perfil del usuario"
            },
            headers=response_headers
        )
        
    rcv_password = dec_rsa_front(user_data.password)
    
    db.update_one({ "email": user_email }, { "$set": { "password": rcv_password } })
    
    log.info("Se ha actualizado la contraseña del usuario: {}".format(user_email))
    
    return JSONResponse(
        status_code=200,
        content={
            "message": "Se ha actualizado correctamente la contraseña"
        }
    )
    
@users_router.patch("/profile")
@dtraia_decorator("api", "users")
def update_user_profile(request: Request, nombre: str = Form(), pfp: Optional[UploadFile] = None, log = None, db = None):
    request_status = validate_request(request)
    if request_status["status"] != 200:
        return JSONResponse(status_code=request_status["status"], content={"error": request_status["error"]})
    response_headers = {"Access-Control-Allow-Origin": "*"}
    user_email = request_status["email"]
    user_info = db.find_one({ "email": user_email }, { "password": 0 })
    if not user_info:
        log.info("Error al recuperar la informacion del usuario {}. El usuario no existe".format(user_email))
        return JSONResponse(
            status_code=404,
            content={
                "error": "Ha ocurrido un error al recuperar el perfil del usuario"
            },
            headers=response_headers
        )
    
    update_params = {
        "nombre": nombre
    }
    
    if pfp:
        save_path = os.path.join(os.getcwd(), "static")
        save_filename = str(user_info["_id"]) + "." + pfp.filename.split(".")[-1]
        with open(os.path.join(save_path, save_filename), "wb") as f:
            pfp.file.seek(0)
            file_content = pfp.file.read()
            f.write(file_content)
        update_params["profilePic"] = save_filename
    
    db.update_one({ "email": user_email }, { "$set": update_params })
        
    user_info = db.find_one({ "email": user_email }, { "_id": 0, "password": 0 })
    
    return JSONResponse(status_code=200, content = {"message": "Se ha actualizado correctamente el perfil", "info": user_info})