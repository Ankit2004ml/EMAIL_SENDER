from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Dict, Any

class EmailSendRequest(BaseModel):
    recipient: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., min_length=1, description="Email subject")
    body: str = Field(..., min_length=1, description="Plain text email body")

    @field_validator("subject", "body")
    @classmethod
    def check_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty or only whitespace")
        return v

class HTMLEmailRequest(BaseModel):
    recipient: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., min_length=1, description="Email subject")
    template_name: str = Field(..., description="Template file name (e.g., welcome.html, otp.html, invoice.html, password_reset.html)")
    template_data: Dict[str, Any] = Field(default_factory=dict, description="Dynamic variables for the template")

    @field_validator("subject", "template_name")
    @classmethod
    def check_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty or only whitespace")
        return v


class SaveTemplateRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Template file name, must end with .html")
    content: str = Field(..., min_length=1, description="HTML content of the template")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v.endswith(".html"):
            raise ValueError("Template name must end with .html")
        return v

