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
def add_router(n, pid):
    routers_response = []
    for _ in range(n):
        router_data = {
            "x": 0,
            "y": 0,
            "compute_id": "local"
        }
        router_url = GNS3_URL + "/projects/{}/templates/{}".format(pid, GNS3_TEMPLATES["router"])
        add_router_response = gns3_session.post(router_url, json=router_data)
        if add_router_response.status_code != 201:
            raise Exception("Ha ocurrido una excepcion: {}".format(json.dumps(new_proj_response.json())))
        device_info = add_router_response.json()
        routers_response.append(device_info)
        print("Respuesta: {}".format(json.dumps(device_info)))
        # Cambiar tarjetas de red
        nic_url = "{}/compute/projects/{}/dynamips/nodes/{}".format(GNS3_URL, pid, device_info["node_id"])
        nic_params = {
            "slot1": "PA-2FE-TX",
            "slot2": "PA-2FE-TX",
            "slot3": "PA-2FE-TX",
            "slot4": "PA-2FE-TX"
        }
        gns3_session.put(nic_url, json=nic_params)
    return routers_response
# Agregar switches
def add_switch(n, pid):
    added_switches = []
    for _ in range(n):
        switch_data = {
            "x": 0,
            "y": 0,
            "compute_id": "local"
        }
        router_url = GNS3_URL + "/projects/{}/templates/{}".format(pid, GNS3_TEMPLATES["switch"])
        add_router_response = gns3_session.post(router_url, json=switch_data)
        if add_router_response.status_code != 201:
            raise Exception("Ha ocurrido una excepcion: {}".format(json.dumps(new_proj_response.json())))
        device_info = add_router_response.json()
        added_switches.append(device_info)
        print("Respuesta: {}".format(json.dumps(device_info)))
    return added_switches
# Conectar dispositivos
def connect_router_to_devices(pid, origin_device, origin_adapter, origin_port, dest_device, dest_adapter, dest_port):
    link_data = {
        "nodes":[{
                "adapter_number": origin_adapter,
                "node_id": origin_device,
                "port_number": origin_port
            },
            {
                "adapter_number": dest_adapter,
                "node_id": dest_device,
                "port_number": dest_port
            }
        ]}
    link_url = GNS3_URL + "/projects/{}/links".format(pid)
    add_link_response = gns3_session.post(link_url, json=link_data)
    if add_link_response.status_code != 201:
        raise Exception("Ha ocurrido una excepcion: {}".format(json.dumps(new_proj_response.json())))
    link_info = add_link_response.json()
    print("Respuesta: {}".format(json.dumps(link_info)))
# Crear un nuevo proyecto
project_config = {
    "name": uuid4().hex[:12]
}
new_proj_response = gns3_session.post(GNS3_URL + "/projects", json=project_config)
if new_proj_response.status_code != 201:
    raise Exception('Ha ocurrido una excepcion: {}'.format(json.dumps(new_proj_response.json())))
project_info = new_proj_response.json()
project_id = project_info["project_id"]
print("Proyecto: {}".format(project_config["name"]))
print('Respuesta: {}'.format(json.dumps(project_info)))
added_routers = add_router(1, project_id)
added_switches = add_switch(1, project_id)
# Conexion entre dispositivos
connect_router_to_devices(project_id, added_routers[0]["node_id"], 0, 0, added_switches[0]["node_id"], 0, 0)
connect_router_to_devices(project_id, added_routers[0]["node_id"], 0, 1, added_switches[0]["node_id"], 0, 1)
