from configparser import ConfigParser
import os, sys

cfg = ConfigParser()

BASE_CONFIG_ROUTE = os.environ["CONFIG_ROUTE"] if os.environ.get("CONFIG_ROUTE") else "/home/ralvarez22/Documentos/dtraia/dtraia_api"

def get_mongo_creds():
    
    cfg.read("{}/config.cfg".format(BASE_CONFIG_ROUTE))
    
    if cfg.has_option("MONGO", "HOST") and cfg.has_option("MONGO", "PORT"):
        host = cfg.get("MONGO", "HOST")
        port = cfg.get("MONGO", "PORT")

        return host, port #user, pwd, host, port
    else:
        print("Config file error: MONGO options not found")
        sys.exit(-1)