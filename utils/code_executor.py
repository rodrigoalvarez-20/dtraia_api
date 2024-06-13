"""
DTRAIA_API - Research Project
Script for execute the generated code by the LLM and take a snapshot of the topolgy.
Authors: Rodrigo Alvarez, Adrian Rodriguez, Uriel Perez
Created on: 2023 
"""

import subprocess
import os
import networkx as nx
import math
from selenium.webdriver import Chrome, ChromeOptions, ChromeService
from selenium.webdriver.common.by import By
from time import sleep
from uuid import uuid4
import requests
import tempfile

static_path = os.environ.get("ROOT_DIR", os.getcwd()) 

TEMPLATE_PATH =  os.path.join(tempfile.gettempdir(), "templates")
TEMPLATE_PATH =  os.path.join(tempfile.gettempdir(), "templates")
TOPOLOGIES_PATH = os.path.join(static_path, "static", "topologies")
GNS3_URL = "http://localhost:3080"

os.makedirs(TEMPLATE_PATH, exist_ok=True)
os.makedirs(TOPOLOGIES_PATH, exist_ok=True)

def write_to_template(code_fragments: str | list[str]):
    """
    Function to write the generated code to a Python executable file for the subprocess command
    Args:
        - code_fragments: String or list of strings with the code to save
    """
    with open(TEMPLATE_PATH + "code_template.py", "w", encoding="utf8") as pf:
        if isinstance(code_fragments, str):
            pf.write(code_fragments)
        else:
            pf.write("\n".join(code_fragments))


def execute_code_template():
    """
    Function to execute the saved code in the executable file.
    Returns:
        - String containing all the outputs of the execution
    """
    return subprocess.run(["python", TEMPLATE_PATH + "code_template.py"], stdout=subprocess.PIPE).stdout.decode()


def download_topology_image(project_id, ss_file):
    """
    Function to take a snapshot of the topology generated. It uses Selenium and Chomedriver as a dependency.
    Args:
        - project_id: ID value of the project created
        - ss_file: Name/Path of the file to save the screenshot
    Returns:
        - status: Boolean value indicating the status of the operation
    """
    opts = ChromeOptions()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("window-size=1920,1080")
    service = ChromeService(os.path.join(static_path, "extras", "chromedriver"))
    driver = Chrome(service=service, options=opts)
    driver.get(GNS3_URL)
    sleep(2)
    driver.get("{}/static/web-ui/server/1/project/{}".format(GNS3_URL, project_id))
    sleep(2)
    driver.find_element(By.XPATH, "/html/body/app-root/div/app-project-map/div/div[1]/div[2]/button[2]").click()
    sleep(2)
    driver.find_element(By.XPATH, "/html/body/app-root/div/app-project-map/div/div[2]/div[1]/button[3]").click()
    return driver.save_screenshot(ss_file)
    

def generate_topology_image(project_id):
    """
    Main function to generate the topology image.
    First load the devices and links in the topology and uses Networkx Spring layout to generate the coords for the devices.
    Second, update the devices properties with the generated coords
    Last, generate the topology image
    Args:
        - project_id: ID value of the GNS3 topology
    Returns:
        - Name of the generated image
    """
    NODES_URL = "{}/v2/projects/{}/nodes".format(GNS3_URL, project_id)
    LINKS_URL = "{}/v2/projects/{}/links".format(GNS3_URL, project_id)
    nodes_data = requests.get(NODES_URL).json()
    links_data = requests.get(LINKS_URL).json()
    graph_nodes = [ (x["node_id"], { "name": x["name"], "node_type": x["node_type"] }) for x in nodes_data]
    graph_edges = [ (x["nodes"][0]["node_id"], x["nodes"][1]["node_id"] ) for x in links_data ]
    # Creación de una instancia de tipo "Grafo"
    G = nx.Graph()
    G.add_nodes_from(graph_nodes)
    G.add_edges_from(graph_edges)
    dis = nx.spring_layout(G, k=-100, scale=130, center=(-200, -200))
    requests.post("{}/v2/projects/{}/open".format(GNS3_URL, project_id))
    for g in graph_nodes:
        position_data = {
            "x": math.ceil(dis[g[0]][0]),
            "y": math.ceil(dis[g[0]][1])
        }
        
        REQ_URL = "{}/v2/projects/{}/nodes/{}".format(GNS3_URL, project_id, g[0])
        _ = requests.put(REQ_URL, json=position_data)
        
    requests.post("{}/v2/projects/{}/close".format(GNS3_URL, project_id))
    generated_image = uuid4().hex[:12]
    png_image = os.path.join(TOPOLOGIES_PATH, generated_image + ".png")
    _ = download_topology_image(project_id, png_image)
    return png_image.split(os.sep)[-1]