from configparser import ConfigParser
import os, sys

cfg = ConfigParser()

BASE_CONFIG_ROUTE = os.environ["CONFIG_ROUTE"] if "CONFIG_ROUTE" in os.environ else os.getcwd()

def get_mongo_creds():
    
    cfg.read("{}/config.cfg".format(BASE_CONFIG_ROUTE))
    
    if cfg.has_option("MONGO", "HOST") and cfg.has_option("MONGO", "PORT"):
        #user = cfg.get("MONGO", "USER")
        #pwd = cfg.get("MONGO", "PASSWORD")
        host = cfg.get("MONGO", "HOST")
        port = cfg.get("MONGO", "PORT")

        return host, port #user, pwd, host, port
    else:
        print("Config file error: MONGO options not found")
        sys.exit(-1)