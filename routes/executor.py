from fastapi import APIRouter, Request, Form, UploadFile
from fastapi.responses import JSONResponse
from datetime import datetime
from uuid import uuid4
import json
import os
## Custom imports
from dtraia_api.models.code import CodeExecution
from dtraia_api.utils.decorators import dtraia_decorator
from dtraia_api.utils.auth import validate_request
from dtraia_api.utils.code_executor import write_to_template, execute_code_template, generate_topology_image

exec_router = APIRouter(prefix="/code")

GNS3_VALIDATION = ["GNS3_URL", "GNS3_TEMPLATES", "http://127.0.0.1:3080/v2"]

@exec_router.post("/execute")
@dtraia_decorator("api", "users")
def execute_python_code(code: CodeExecution, request: Request, db = None, log = None):
    request_status = validate_request(request)
    if request_status["status"] != 200:
        return JSONResponse(status_code=request_status["status"], content={"error": request_status["error"]})

    
    is_for_gns3 = False
    for gns3_code in GNS3_VALIDATION:
        is_for_gns3 = any(gns3_code in x for x in code.code_fragments)
    
    write_to_template(code.code_fragments)
    code_exec_output = execute_code_template()
    
    code_response = {
        "message": "Se ha ejecutado correctamente el código",
        "output": code_exec_output,
        "can_take_photo": is_for_gns3
    }
    
    return JSONResponse(status_code=200,content=code_response)

@exec_router.get("/network")
@dtraia_decorator("api", None)
def get_topology_image( project_id:str, request: Request, log = None):
    request_status = validate_request(request)
    if request_status["status"] != 200:
        return JSONResponse(status_code=request_status["status"], content={"error": request_status["error"]})
    
    generated_image = generate_topology_image(project_id)
    
    return JSONResponse(status_code=200, 
                        content={ 
                                 "message": "Se ha generado correctamente la imagen de la topologia", 
                                 "image": "/api/static/topologies/{}".format(generated_image) 
                            }
                        )
    
    
