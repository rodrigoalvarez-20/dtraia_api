from pydantic import BaseModel


class LoginUserModel(BaseModel):
    email: str
    password: str
    

class RegisterUserModel(BaseModel):
    nombre: str
    email: str
    password: str
