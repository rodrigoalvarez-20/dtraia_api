import pexpect
import requests
from uuid import uuid4
import json
from time import sleep

GNS3_URL = "http://127.0.0.1:3080/v2"
gns3_session = requests.Session()
gns3_session.headers["Content-Type"] = "application/json"

# Crear un nuevo proyecto
project_config = {
    "name": uuid4().hex[:12]
}
new_proj_response = gns3_session.post(GNS3_URL + "/projects", json=project_config)
if new_proj_response.status_code != 201:
    raise Exception('Ha ocurrido una excepcion: {}'.format(json.dumps(new_proj_response.json())))
project_info = new_proj_response.json()
print('Respuesta: {}'.format(json.dumps(project_info)))

# Agregar un router
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

# Encender router
start_node_url = GNS3_URL + "/projects/{}/nodes/{}/start".format(device_info["project_id"], device_info["node_id"])
start_node_response = gns3_session.post(start_node_url, json={})
if start_node_response.status_code != 200:
    raise Exception("Ha ocurrido una excepcion: {}".format(json.dumps(start_node_response.json())))
print("Respuesta: {}".format(json.dumps(start_node_response.json())))

# Mostrar configuracion del router
device_telnet = pexpect.spawn("telnet", ["127.0.0.1", str(device_info["console"])], encoding="utf-8")
device_telnet.sendline("\r\n")
sleep(5)
device_telnet.expect("#", 10)
device_telnet.sendline("terminal length 0\r\n")
device_telnet.expect("#", 10)
device_telnet.sendline("sh run\r\n")
device_telnet.expect("#", 10)
print("Respuesta: {}".format(device_telnet.before))
device_telnet.close()