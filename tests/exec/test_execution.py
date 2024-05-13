import requests
from uuid import uuid4
import json
GNS3_URL = "http://127.0.0.1:3080/v2"
GNS3_TEMPLATES = {
    "router": "61909209-f885-40e9-9922-b1e9e03d2034",
    "switch": "1966b864-93e7-32d5-965f-001384eec461",
    "vpc": "19021f99-e36f-394d-b4a1-8aaa902ab9cc"
}
gns3_session = requests.Session()
gns3_session.headers["Content-Type"] = "application/json"
# Agregar un router
def add_router(n):
    for _ in range(n):
        router_data = {
            "x": 0,
            "y": 0,
            "compute_id": "local"
        }
        router_url = GNS3_URL + "/projects/{}/templates/61909209-f885-40e9-9922-b1e9e03d2034".format(project_info["project_id"])
        add_router_response = gns3_session.post(router_url, json=router_data)
        if add_router_response.status_code != 201:
            raise Exception("Ha ocurrido una excepcion: {}".format(json.dumps(new_proj_response.json())))
        device_info = add_router_response.json()
        print("Respuesta: {}".format(json.dumps(device_info)))
# Agregar switches
def add_switch(n):
    for _ in range(n):
        switch_data = {
            "x": 0,
            "y": 0,
            "compute_id": "local"
        }
        router_url = GNS3_URL + "/projects/{}/templates/{}".format(project_info["project_id"], GNS3_TEMPLATES["switch"])
        add_router_response = gns3_session.post(router_url, json=switch_data)
        if add_router_response.status_code != 201:
            raise Exception("Ha ocurrido una excepcion: {}".format(json.dumps(new_proj_response.json())))
        device_info = add_router_response.json()
        print("Respuesta: {}".format(json.dumps(device_info)))
        
# Agregar VirtualPC
def add_virtualpc(n):
    for _ in range(n):
        router_data = {
            "x": 0,
            "y": 0,
            "compute_id": "local"
        }
        router_url = GNS3_URL + "/projects/{}/templates/{}".format(project_info["project_id"], GNS3_TEMPLATES["vpc"])
        add_router_response = gns3_session.post(router_url, json=router_data)
        if add_router_response.status_code != 201:
            raise Exception("Ha ocurrido una excepcion: {}".format(json.dumps(new_proj_response.json())))
        device_info = add_router_response.json()
        print("Respuesta: {}".format(json.dumps(device_info)))
# Crear un nuevo proyecto
project_config = {
    "name": uuid4().hex[:12]
}
new_proj_response = gns3_session.post(GNS3_URL + "/projects", json=project_config)
if new_proj_response.status_code != 201:
    raise Exception('Ha ocurrido una excepcion: {}'.format(json.dumps(new_proj_response.json())))
project_info = new_proj_response.json()
print('Respuesta: {}'.format(json.dumps(project_info)))
add_router(3)
add_switch(2)
add_virtualpc(1)