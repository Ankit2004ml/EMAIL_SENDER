import os
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from fastapi import UploadFile, HTTPException
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from app.config import settings
from app.logger import log_success, log_failed

# Base Provider Abstract Interface for Extensibility
class BaseEmailProvider(ABC):
    @abstractmethod
    async def send_plain_email(self, recipient: str, subject: str, body: str) -> dict:
        pass

    @abstractmethod
    async def send_html_email(self, recipient: str, subject: str, template_name: str, template_data: dict) -> dict:
        pass

    @abstractmethod
    async def send_email_with_attachment(self, recipient: str, subject: str, body: str, file: UploadFile) -> dict:
        pass

    @abstractmethod
    async def send_html_email_with_attachment(self, recipient: str, subject: str, template_name: str, template_data: dict, file: Optional[UploadFile] = None, templates_dir: Optional[str] = None) -> dict:
        pass


# SMTP Implementation using FastAPI-Mail
class SMTPEmailProvider(BaseEmailProvider):
    def __init__(self):
        # Configure Jinja2 Environment
        self.templates_dir = os.path.join(settings.BASE_DIR, "app", "templates")
        os.makedirs(self.templates_dir, exist_ok=True)
        self.jinja_env = Environment(loader=FileSystemLoader(self.templates_dir))
        
        # Configure FastAPI-Mail connection settings
        # Note: If credentials are empty, USE_CREDENTIALS should be false to prevent startup issues on local/fake SMTP
        use_credentials = bool(settings.MAIL_USERNAME and settings.MAIL_PASSWORD)
        
        self.conf = ConnectionConfig(
            MAIL_USERNAME=settings.MAIL_USERNAME,
            MAIL_PASSWORD=settings.MAIL_PASSWORD,
            MAIL_FROM=settings.MAIL_FROM or settings.MAIL_USERNAME or "noreply@example.com",
            MAIL_PORT=settings.MAIL_PORT,
            MAIL_SERVER=settings.MAIL_SERVER,
            MAIL_FROM_NAME=settings.APP_NAME,
            MAIL_STARTTLS=settings.MAIL_STARTTLS,
            MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
            USE_CREDENTIALS=use_credentials,
            VALIDATE_CERTS=use_credentials
        )
        self.fastmail = FastMail(self.conf)

    async def send_plain_email(self, recipient: str, subject: str, body: str) -> dict:
        message = MessageSchema(
            subject=subject,
            recipients=[recipient],
            body=body,
            subtype="plain"
        )
        start_time = time.time()
        try:
            await self.fastmail.send_message(message)
            elapsed = time.time() - start_time
            log_success(recipient, subject, "SMTP", elapsed, body=body)
            return {"success": True, "message": "Plain text email sent successfully"}
        except Exception as e:
            log_failed(recipient, str(e), "SMTP", subject=subject, body=body)
            raise HTTPException(
                status_code=500,
                detail=f"SMTP Error: {str(e)}"
            )

    async def send_html_email(self, recipient: str, subject: str, template_name: str, template_data: dict) -> dict:
        try:
            # Recreate Jinja2 environment to ensure newly saved templates are reloadable
            self.jinja_env = Environment(loader=FileSystemLoader(self.templates_dir))
            template = self.jinja_env.get_template(template_name)
            html_content = template.render(**template_data)
        except TemplateNotFound:
            log_failed(recipient, f"Template '{template_name}' not found", "SMTP", subject=subject, template_name=template_name, template_data=template_data)
            raise HTTPException(
                status_code=404,
                detail=f"HTML Template '{template_name}' not found."
            )
        except Exception as e:
            log_failed(recipient, f"Template rendering error: {str(e)}", "SMTP", subject=subject, template_name=template_name, template_data=template_data)
            raise HTTPException(
                status_code=500,
                detail=f"Template rendering failed: {str(e)}"
            )

        message = MessageSchema(
            subject=subject,
            recipients=[recipient],
            body=html_content,
            subtype="html"
        )
        
        start_time = time.time()
        try:
            await self.fastmail.send_message(message)
            elapsed = time.time() - start_time
            log_success(recipient, subject, "SMTP", elapsed, body=html_content, template_name=template_name, template_data=template_data)
            return {"success": True, "message": f"HTML email ({template_name}) sent successfully"}
        except Exception as e:
            log_failed(recipient, str(e), "SMTP", subject=subject, body=html_content, template_name=template_name, template_data=template_data)
            raise HTTPException(
                status_code=500,
                detail=f"SMTP Error: {str(e)}"
            )

    async def send_html_email_with_attachment(self, recipient: str, subject: str, template_name: str, template_data: dict, file: Optional[UploadFile] = None, templates_dir: Optional[str] = None) -> dict:
        try:
            # Recreate Jinja2 environment to ensure newly saved templates are reloadable
            target_dir = templates_dir or self.templates_dir
            self.jinja_env = Environment(loader=FileSystemLoader(target_dir))
            template = self.jinja_env.get_template(template_name)
            html_content = template.render(**template_data)
        except TemplateNotFound:
            log_failed(recipient, f"Template '{template_name}' not found", "SMTP", subject=subject, template_name=template_name, template_data=template_data, attachment_name=file.filename if file else None)
            raise HTTPException(
                status_code=404,
                detail=f"HTML Template '{template_name}' not found."
            )
        except Exception as e:
            log_failed(recipient, f"Template rendering error: {str(e)}", "SMTP", subject=subject, template_name=template_name, template_data=template_data, attachment_name=file.filename if file else None)
            raise HTTPException(
                status_code=500,
                detail=f"Template rendering failed: {str(e)}"
            )

        attachments = [file] if file else []
        message = MessageSchema(
            subject=subject,
            recipients=[recipient],
            body=html_content,
            subtype="html",
            attachments=attachments
        )
        
        start_time = time.time()
        try:
            await self.fastmail.send_message(message)
            elapsed = time.time() - start_time
            log_success(recipient, subject, "SMTP", elapsed, body=html_content, template_name=template_name, template_data=template_data, attachment_name=file.filename if file else None)
            return {"success": True, "message": f"HTML email ({template_name}) sent successfully"}
        except Exception as e:
            log_failed(recipient, str(e), "SMTP", subject=subject, body=html_content, template_name=template_name, template_data=template_data, attachment_name=file.filename if file else None)
            raise HTTPException(
                status_code=500,
                detail=f"SMTP Error: {str(e)}"
            )

    async def send_email_with_attachment(self, recipient: str, subject: str, body: str, file: UploadFile) -> dict:
        if not file.filename:
            log_failed(recipient, "Missing attachment filename", "SMTP", subject=subject, body=body)
            raise HTTPException(
                status_code=400,
                detail="Attachment has no valid filename."
            )

        message = MessageSchema(
            subject=subject,
            recipients=[recipient],
            body=body,
            subtype="plain",
            attachments=[file]
        )
        
        start_time = time.time()
        try:
            await self.fastmail.send_message(message)
            elapsed = time.time() - start_time
            log_success(recipient, subject, "SMTP", elapsed, body=body, attachment_name=file.filename)
            return {"success": True, "message": "Email with attachment sent successfully"}
        except Exception as e:
            log_failed(recipient, str(e), "SMTP", subject=subject, body=body, attachment_name=file.filename)
            raise HTTPException(
                status_code=500,
                detail=f"SMTP Error: {str(e)}"
            )


# Factory function to support multiple email providers in the future
def get_email_provider() -> BaseEmailProvider:
    provider_name = settings.EMAIL_PROVIDER.lower()
    if provider_name == "smtp":
        return SMTPEmailProvider()
    else:
        # Log error or raise Exception for unsupported provider
        raise ValueError(f"Email provider '{provider_name}' is not supported.")
