from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserCreate(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str
    tipo_consultor: Optional[str] = None
    telefone: Optional[str] = None

class UserUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[str] = None
    tipo_consultor: Optional[str] = None
    telefone: Optional[str] = None
