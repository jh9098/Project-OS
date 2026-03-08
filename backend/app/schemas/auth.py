from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class UserMe(BaseModel):
    id: str
    username: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user: UserMe
