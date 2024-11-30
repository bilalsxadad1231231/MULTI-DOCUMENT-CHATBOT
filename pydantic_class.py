from pydantic import Field, BaseModel,EmailStr
from datetime import datetime

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserInDB(UserBase):
    id: int
    password_hash: str
    created_at: datetime

class ChatRequest(BaseModel):
    chatbot_name: str
    message: str
    
class ChatbotCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., max_length=500)
    persona_prompt: str = Field(..., max_length=1000)

class ChatbotResponse(BaseModel):
    id: int
    name: str
    description: str
    persona_prompt: str
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
