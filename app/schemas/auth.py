from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    city: str = ""  # required for city-scoped admin accounts


class OtpSendRequest(BaseModel):
    phone: str
    purpose: str = "register"  # register | inquiry | vendor_register


class OtpVerifyRequest(BaseModel):
    phone: str
    code: str
    purpose: str = "register"


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
    phone_otp: str = ""


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str


class RefreshRequest(BaseModel):
    refresh_token: str
