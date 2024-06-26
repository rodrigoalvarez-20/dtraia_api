import requests
import pexpect
from uuid import uuid4
import json
from time import sleep
GNS3_URL = "http://127.0.0.1:3080/v2"
GNS3_TEMPLATES = {
    "router": "61909209-f885-40e9-9922-b1e9e03d2034",
    "switch": "1966b864-93e7-32d5-965f-001384eec461",
    "vpc": "19021f99-e36f-394d-b4a1-8aaa902ab9cc"
}
gns3_session = requests.Session()
gns3_session.headers["Content-Type"] = "application/json"
def exec_command(session, command):
    session.sendline(command + "\r\n")
    session.expect("#", 10)
    session.sendline("\r\n")
    session.expect("#", 10)
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
# Agregar VirtualPC
def add_virtualpc(n, pid):
    added_vpcs = []
    for _ in range(n):
        router_data = {
            "x": 0,
            "y": 0,
            "compute_id": "local"
        }
        router_url = GNS3_URL + "/projects/{}/templates/{}".format(pid, GNS3_TEMPLATES["vpc"])
        add_router_response = gns3_session.post(router_url, json=router_data)
        if add_router_response.status_code != 201:
            raise Exception("Ha ocurrido una excepcion: {}".format(json.dumps(new_proj_response.json())))
        device_info = add_router_response.json()
        added_vpcs.append(device_info)
        print("Respuesta: {}".format(json.dumps(device_info)))
    return added_vpcs
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
# Encender dispositivo
def power_device(pid, node_id):
    power_url = GNS3_URL + "/projects/{}/nodes/{}/start".format(pid, node_id)
    power_response = gns3_session.post(power_url, json={})
    if power_response.status_code != 200:
        raise Exception("Ha ocurrido una excepcion: {}".format(json.dumps(power_response.json())))
    print("Respuesta: Se ha encendido el dispositivo {}".format(node_id))
def execute_router_commands(telnet_port, cmd_list):
    device_telnet = pexpect.spawn("telnet", ["127.0.0.1", telnet_port], encoding="utf-8")
    device_telnet.sendline("\r\n")
    sleep(5)
    _ = [ exec_command(device_telnet, cmd) for cmd in cmd_list ]
    device_telnet.close()
def execute_vpc_commands(telnet_port, cmd_list):
    device_telnet = pexpect.spawn("telnet", ["127.0.0.1", telnet_port], encoding="utf-8")
    sleep(5)
    device_telnet.sendline("\n")
    device_telnet.sendline("\n")
    device_telnet.expect(">", 10)
    for cmd in cmd_list:
        device_telnet.sendline(cmd + "\n")
        sleep(3)
    device_telnet.close()
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
added_routers = add_router(2, project_id)
added_switches = add_switch(1, project_id)
added_vpcs = add_virtualpc(3, project_id)
# Conexion entre dispositivos
connect_router_to_devices(project_id, added_routers[0]["node_id"], 0, 0, added_switches[0]["node_id"], 0, 0)
connect_router_to_devices(project_id, added_routers[1]["node_id"], 0, 0, added_switches[0]["node_id"], 0, 1)
connect_router_to_devices(project_id, added_switches[0]["node_id"], 0, 2, added_vpcs[0]["node_id"], 0, 0)
connect_router_to_devices(project_id, added_switches[0]["node_id"], 0, 3, added_vpcs[1]["node_id"], 0, 0)
connect_router_to_devices(project_id, added_switches[0]["node_id"], 0, 4, added_vpcs[2]["node_id"], 0, 0)
# Encender dispositivos
_ = [ power_device(project_id, x["node_id"]) for x in added_routers ]
_ = [ power_device(project_id, x["node_id"]) for x in added_vpcs ]
sleep(5)
execute_router_commands(str(added_routers[0]["console"]), ["conf t", "int f0/0", "ip addr 200.100.0.1 255.255.255.0", "no shut", "router rip", "ver 2", "net 200.100.0.0"])
execute_router_commands(str(added_routers[1]["console"]), ["conf t", "int f0/0", "ip addr 200.100.0.2 255.255.255.0", "no shut", "router rip", "ver 2", "net 200.100.0.0"])
execute_vpc_commands(str(added_vpcs[0]["console"]), ["\n","ip 200.100.0.10 255.255.255.0"])
execute_vpc_commands(str(added_vpcs[1]["console"]), ["\n","ip 200.100.0.13 255.255.255.0"])
execute_vpc_commands(str(added_vpcs[2]["console"]), ["\n","ip 200.100.0.20 255.255.255.0"])