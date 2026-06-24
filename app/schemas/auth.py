from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterUserRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str = ""
    city: str = ""
    role: str = "client"


class RegisterVendorRequest(BaseModel):
    name: str
    company: str
    email: EmailStr
    password: str
    phone: str = ""
    city: str = ""
    category: str = ""


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str


class RefreshRequest(BaseModel):
    refresh_token: str
