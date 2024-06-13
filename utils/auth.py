"""
DTRAIA_API - Research Project
Script for AUTH utils like signing Token and validate it
Authors: Rodrigo Alvarez, Adrian Rodriguez, Uriel Perez
Created on: 2023 
"""
from fastapi import Request
import random
import jwt
import random
from datetime import datetime, timezone, timedelta

## Custom imports 
from dtraia_api.utils.common import load_private_key, get_raw_private_key, get_raw_public_key

def generate_login_token(id: str, email : str, htl = 4):
    """
    This function allows to create a JWT with the user info passed.
    Args:
        - id: User id in database
        - email: User email in database
        - htl: Time in hour for the expiricy of the token
    Returns:
    - tk: String containing the JWT value
    """
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
    """
    Function to auth a user request. It validates the sign of the JWT and the expiricy date
    Args:
        - token: JWT value
    Returns:
        - Dict-Like response with status and data
            - 200 -> Valid Token, User info returned
            - 401 -> The token has expired
            - 400 -> The token is invalid / Malformed Token
    """
    try:
        public_key = get_raw_public_key(load_private_key()).decode()
        decoded = jwt.decode(token, public_key, algorithms=["RS256"])
        return {"status": 200, **decoded}  
    except jwt.ExpiredSignatureError:
        return { "status": 401, "error": "La token ha expirado" }
    except jwt.PyJWTError as error:
        return {"status": 400, "error": str(error)}


def validate_request(request: Request):
    """
    Base function for the User request Auth. It validates the existence of "Authorization" header and the Token in it.
    Args:
        - request: FastAPI Request for getting the headers value
    Returns:
        - Dict-Like response containing status and information about the operation
            - 400 --> The "Authorization" field not found in the headers
            - auth-respose --> Auth Function response dict
    """
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