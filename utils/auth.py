from fastapi import Request
from os import getcwd
from typing import Dict
import random
import jwt
import random
from datetime import datetime, timezone, timedelta


## Custom imports 

from dtraia_api.utils.common import load_private_key, get_raw_private_key, get_raw_public_key

# TODO Firmar con email + id y agregar el tiempo de duracion
def generate_login_token(id: str, email : str, htl = 4):
    exp_date = datetime.now(tz=timezone.utc) + timedelta(hours=htl)
    payload = {
        "id": id,
        "email": email,
        "rd": random.randint(0, 1000000),
        "exp": exp_date
    }

    private_key = load_private_key()
    private_key_raw = get_raw_private_key(private_key).decode()
    
    tk = jwt.encode(payload, private_key_raw, algorithm="RS256")
    
    return tk
    
    

def auth(token: str):
    try:
        public_key = get_raw_public_key(load_private_key()).decode()
        decoded = jwt.decode(token, public_key, algorithms=["RS256"])
        return {"status": 200, **decoded}  
    except jwt.ExpiredSignatureError:
        return { "status": 401, "error": "La token ha expirado" }
    except jwt.PyJWTError as error:
        return {"status": 400, "error": str(error)}


def validate_request(request: Request):
    if "Authorization" not in request.headers:
        return {"status": 400, "error": "Encabezado no encontrado"}
    else:
        return auth(request.headers["Authorization"])
    
    
if __name__ == "__main__":
    tk = generate_login_token("00001", "rodrigoalvarez449@gmail.com")
    from time import sleep
    sleep(15)
    dec_tk = auth(tk)
    
    print(dec_tk)