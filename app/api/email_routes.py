from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from pydantic import EmailStr, ValidationError, TypeAdapter

from app.schemas.email_schema import EmailSendRequest, HTMLEmailRequest, SaveTemplateRequest
from app.services.email_service import get_email_provider, BaseEmailProvider
from app.utils.validators import validate_attachment
from app.config import settings

router = APIRouter()

email_adapter = TypeAdapter(EmailStr)

@router.get("/api")
async def root():
    return {
        "success": True,
        "message": f"Welcome to the {settings.APP_NAME}",
        "docs": "/docs",
        "health": "/health"
    }

@router.get("/health")
async def health_check():
    # Simple check, in production you might ping the SMTP connection
    return {
        "status": "healthy",
        "provider": settings.EMAIL_PROVIDER,
        "app": settings.APP_NAME
    }

@router.post("/send-email")
async def send_plain_email(
    request: EmailSendRequest,
    provider: BaseEmailProvider = Depends(get_email_provider)
):
    return await provider.send_plain_email(
        recipient=request.recipient,
        subject=request.subject,
        body=request.body
    )

@router.post("/send-html-email")
async def send_html_email(
    request: HTMLEmailRequest,
    provider: BaseEmailProvider = Depends(get_email_provider)
):
    return await provider.send_html_email(
        recipient=request.recipient,
        subject=request.subject,
        template_name=request.template_name,
        template_data=request.template_data
    )

@router.post("/send-email-with-attachment")
async def send_email_with_attachment(
    recipient: str = Form(..., description="Recipient email address"),
    subject: str = Form(..., description="Email subject"),
    body: str = Form(..., description="Email body / message"),
    file: UploadFile = File(..., description="File to attach"),
    provider: BaseEmailProvider = Depends(get_email_provider)
):
    # Validate recipient email address
    try:
        validated_recipient = email_adapter.validate_python(recipient)
    except ValidationError:
        raise HTTPException(status_code=400, detail="Invalid email format.")

    # Validate subject and body presence
    if not subject.strip():
        # Match standard fastapi validation structure
        raise HTTPException(status_code=422, detail="Subject is required and cannot be empty.")
    if not body.strip():
        raise HTTPException(status_code=400, detail="Body/message is required and cannot be empty.")

    # Validate attachment (size, type)
    validate_attachment(file)

    return await provider.send_email_with_attachment(
        recipient=validated_recipient,
        subject=subject,
        body=body,
        file=file
    )


@router.get("/api/logs")
async def get_logs():
    import os
    import sqlite3
    db_file_path = os.path.join(settings.LOGS_DIR, "email_history.db")
    if not os.path.exists(db_file_path):
        return {"success": True, "logs": []}
    
    try:
        conn = sqlite3.connect(db_file_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Fetch the last 50 entries
        cursor.execute("""
            SELECT id, timestamp, recipient, subject, body, template_name, template_data, attachment_name, status, provider, response_time, error_message
            FROM email_logs
            ORDER BY id DESC
            LIMIT 50
        """)
        rows = cursor.fetchall()
        logs = [dict(row) for row in rows]
        conn.close()
        return {"success": True, "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch logs from database: {str(e)}")


@router.get("/api/templates")
async def get_templates():
    import os
    templates_dir = os.path.join(settings.BASE_DIR, "app", "templates")
    if not os.path.exists(templates_dir):
        return {"success": True, "templates": []}
    try:
        files = [f for f in os.listdir(templates_dir) if f.endswith(".html")]
        return {"success": True, "templates": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list templates: {str(e)}")


@router.get("/api/templates/{name}")
async def get_template_content(name: str):
    import os
    templates_dir = os.path.join(settings.BASE_DIR, "app", "templates")
    file_path = os.path.join(templates_dir, os.path.basename(name))
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Template not found")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"success": True, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read template: {str(e)}")


@router.post("/api/templates")
async def save_template(request: SaveTemplateRequest):
    import os
    templates_dir = os.path.join(settings.BASE_DIR, "app", "templates")
    os.makedirs(templates_dir, exist_ok=True)
    
    filename = os.path.basename(request.name)
    if not filename.endswith(".html"):
        raise HTTPException(status_code=400, detail="Invalid template name. Must end with .html")
        
    file_path = os.path.join(templates_dir, filename)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(request.content)
        return {"success": True, "message": f"Template '{filename}' saved successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save template: {str(e)}")


@router.post("/send-html-email-with-attachment")
async def send_html_email_with_attachment(
    recipient: str = Form(..., description="Recipient email address"),
    subject: str = Form(..., description="Email subject"),
    template_name: str = Form(..., description="Template file name"),
    template_data_json: str = Form(..., description="JSON string containing template variables mapping"),
    file: Optional[UploadFile] = File(default=None, description="Optional file to attach"),
    provider: BaseEmailProvider = Depends(get_email_provider)
):
    import json
    try:
        validated_recipient = email_adapter.validate_python(recipient)
    except ValidationError:
        raise HTTPException(status_code=400, detail="Invalid email format.")

    if not subject.strip():
        raise HTTPException(status_code=422, detail="Subject is required.")
    if not template_name.strip():
        raise HTTPException(status_code=400, detail="Template name is required.")

    try:
        template_data = json.loads(template_data_json) if template_data_json else {}
        if not isinstance(template_data, dict):
            raise ValueError()
    except Exception:
        raise HTTPException(status_code=400, detail="template_data_json must be a valid JSON object string.")

    if file and file.filename:
        validate_attachment(file)

    return await provider.send_html_email_with_attachment(
        recipient=validated_recipient,
        subject=subject,
        template_name=template_name,
        template_data=template_data,
        file=file
    )


async def process_bulk_emails(
    recipients_list: list,
    subject: str,
    body: Optional[str],
    template_name: Optional[str],
    template_data: dict,
    file_bytes: Optional[bytes],
    file_name: Optional[str],
    file_content_type: Optional[str],
    provider: BaseEmailProvider
):
    import io
    from fastapi import UploadFile
    from pydantic import EmailStr, ValidationError
    from app.logger import log_failed
    
    for recipient_email in recipients_list:
        recipient_email = recipient_email.strip()
        if not recipient_email:
            continue
        
        try:
            validated_recipient = email_adapter.validate_python(recipient_email)
        except ValidationError as e:
            log_failed(recipient_email, f"Invalid email format: {str(e)}", "SMTP", subject=subject, body=body, template_name=template_name, template_data=template_data, attachment_name=file_name)
            continue
            
        attached_file = None
        if file_bytes is not None and file_name:
            attached_file = UploadFile(
                filename=file_name,
                file=io.BytesIO(file_bytes),
                headers={"content-type": file_content_type or "application/octet-stream"}
            )
            
        try:
            if template_name:
                import os
                bulk_templates_dir = os.path.join(settings.BASE_DIR, "app", "bulk_templates")
                await provider.send_html_email_with_attachment(
                    recipient=validated_recipient,
                    subject=subject,
                    template_name=template_name,
                    template_data=template_data,
                    file=attached_file,
                    templates_dir=bulk_templates_dir
                )
            elif attached_file:
                await provider.send_email_with_attachment(
                    recipient=validated_recipient,
                    subject=subject,
                    body=body or "",
                    file=attached_file
                )
            else:
                await provider.send_plain_email(
                    recipient=validated_recipient,
                    subject=subject,
                    body=body or ""
                )
        except Exception:
            pass


@router.post("/send-bulk-email", status_code=202)
async def send_bulk_email(
    background_tasks: BackgroundTasks,
    recipients: Optional[str] = Form(None, description="Comma-separated list of emails"),
    recipients_file: Optional[UploadFile] = File(None, description="Optional text or CSV file containing emails"),
    subject: str = Form(..., description="Email subject"),
    body: Optional[str] = Form(None, description="Email plain text body"),
    template_name: Optional[str] = Form(None, description="Template file name"),
    template_data_json: Optional[str] = Form(None, description="JSON string containing template variable mappings"),
    file: Optional[UploadFile] = File(None, description="Optional attachment file"),
    provider: BaseEmailProvider = Depends(get_email_provider)
):
    import json
    
    email_list = []
    
    if recipients:
        email_list.extend([e.strip() for e in recipients.split(",") if e.strip()])
        
    if recipients_file:
        try:
            content = await recipients_file.read()
            text = content.decode("utf-8")
            for line in text.splitlines():
                for part in line.split(","):
                    part = part.strip()
                    if part:
                        email_list.append(part)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read recipients file: {str(e)}")
            
    email_list = list(dict.fromkeys(email_list))
    
    if not email_list:
        raise HTTPException(status_code=400, detail="No recipients provided. Supply recipients list or upload a file.")
        
    template_data = {}
    if template_data_json:
        try:
            template_data = json.loads(template_data_json)
            if not isinstance(template_data, dict):
                raise ValueError()
        except Exception:
            raise HTTPException(status_code=400, detail="template_data_json must be a valid JSON object string.")
            
    file_bytes = None
    file_name = None
    file_content_type = None
    if file and file.filename:
        try:
            file_bytes = await file.read()
            file_name = file.filename
            file_content_type = file.content_type
            import io
            test_file = UploadFile(
                filename=file_name,
                file=io.BytesIO(file_bytes),
                headers={"content-type": file_content_type or "application/octet-stream"}
            )
            validate_attachment(test_file)
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read attachment: {str(e)}")
            
    background_tasks.add_task(
        process_bulk_emails,
        recipients_list=email_list,
        subject=subject,
        body=body,
        template_name=template_name,
        template_data=template_data,
        file_bytes=file_bytes,
        file_name=file_name,
        file_content_type=file_content_type,
        provider=provider
    )
    
    return {
        "success": True,
        "message": f"Bulk sending scheduled successfully for {len(email_list)} recipients in the background.",
        "recipients_count": len(email_list)
    }


@router.get("/api/bulk-templates")
async def get_bulk_templates():
    import os
    templates_dir = os.path.join(settings.BASE_DIR, "app", "bulk_templates")
    os.makedirs(templates_dir, exist_ok=True)
    try:
        files = [f for f in os.listdir(templates_dir) if f.endswith(".html")]
        return {"success": True, "templates": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list bulk templates: {str(e)}")


@router.get("/api/bulk-templates/{name}")
async def get_bulk_template_content(name: str):
    import os
    templates_dir = os.path.join(settings.BASE_DIR, "app", "bulk_templates")
    file_path = os.path.join(templates_dir, os.path.basename(name))
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Bulk Template not found")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"success": True, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read bulk template: {str(e)}")


@router.post("/api/bulk-templates")
async def save_bulk_template(request: SaveTemplateRequest):
    import os
    templates_dir = os.path.join(settings.BASE_DIR, "app", "bulk_templates")
    os.makedirs(templates_dir, exist_ok=True)
    
    filename = os.path.basename(request.name)
    if not filename.endswith(".html"):
        raise HTTPException(status_code=400, detail="Invalid template name. Must end with .html")
        
    file_path = os.path.join(templates_dir, filename)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(request.content)
        return {"success": True, "message": f"Bulk template '{filename}' saved successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save bulk template: {str(e)}")




