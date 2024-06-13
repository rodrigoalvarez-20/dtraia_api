"""
DTRAIA_API - Research Project
Script for loading the Config file for MongoDB or Email credentials
Authors: Rodrigo Alvarez, Adrian Rodriguez, Uriel Perez
Created on: 2023 
"""

from configparser import ConfigParser
import os, sys

cfg = ConfigParser()

BASE_CONFIG_ROUTE = os.environ["CONFIG_ROUTE"] if os.environ.get("CONFIG_ROUTE") else "./dtraia_api"

def get_mongo_creds():
    
    cfg.read("{}/config.cfg".format(BASE_CONFIG_ROUTE))
    
    if cfg.has_option("MONGO", "HOST") and cfg.has_option("MONGO", "PORT"):
        host = cfg.get("MONGO", "HOST")
        port = cfg.get("MONGO", "PORT")

        return host, port #user, pwd, host, port
    else:
        print("Config file error: MONGO options not found")
        sys.exit(-1)
        
def get_email_creds():
    cfg.read("{}/config.cfg".format(BASE_CONFIG_ROUTE))
    
    if cfg.has_option("EMAIL", "CORREO") and cfg.has_option("EMAIL", "PWD"):
        email = cfg.get("EMAIL", "CORREO")
        pwd = cfg.get("EMAIL", "PWD")

        return email, pwd
    else:
        print("Config file error: EMAIL options not found")
        sys.exit(-1)