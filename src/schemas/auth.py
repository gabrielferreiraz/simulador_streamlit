from pydantic import BaseModel, EmailStr, Field

class LoginInput(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1) # Senha não pode ser vazia
