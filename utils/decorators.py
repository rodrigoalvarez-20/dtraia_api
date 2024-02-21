from functools import wraps
from datetime import datetime
import logging
import os, sys

# Custom imports
from dtraia_api.utils.mongo import get_mongo_connection

# Tipos de logs para la aplicacion
# 1. API
# 2. Users
# 3. LLM
# 4. General

LOGS_FOLDER = os.environ.get("LOGS_PATH") if "LOGS_PATH" in os.environ else os.getcwd()

BASE_PATH = LOGS_FOLDER + "/logs"

if not os.path.isdir(BASE_PATH):
    os.mkdir(BASE_PATH)

routes = {
    "api": f"{BASE_PATH}/api_general",
    "users": f"{BASE_PATH}/users",
    "llm": f"{BASE_PATH}/llm",
    "general": f"{BASE_PATH}/dtraia"
}

def dtraia_decorator(log_alias = None, mongo_alias = None, mongo_connection = False):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                if log_alias is not None:
                    filename = "DTRAIA_{}_LOG_{}.log".format(log_alias.upper(), datetime.now().strftime('%Y_%m_%d'))
                    path_to_log = routes[log_alias] if log_alias in routes else routes["api"]
                    os.makedirs(path_to_log, exist_ok=True)
                    path_to_log += "/" + filename
                    #print(path_to_log)
                    
                    logging.basicConfig(
                    format="=== %(asctime)s::%(levelname)s::%(funcName)s === %(message)s", filename=path_to_log, level=logging.DEBUG)
                    log = logging.getLogger("DTRAIA_SERVICE")
                    
                kwargs["log"] = log

                if mongo_alias is not None:
                    mongo_con = get_mongo_connection()
                    kwargs["db"] = mongo_con["dtraia"][mongo_alias] if not mongo_connection else mongo_con["dtraia"]
                    
            except Exception as ex:
                print(ex)
                #send_telegram_notification("CRITICAL", f"Ha ocurrido un error en el decorador: {ex}", "Decorator")
                sys.exit(-1)
            return func(*args, **kwargs)
        return wrapper
    return decorator