import io
import os
import sqlite3
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

def get_db_log_count():
    db_file_path = os.path.join(settings.LOGS_DIR, "email_history.db")
    if not os.path.exists(db_file_path):
        return 0
    try:
        conn = sqlite3.connect(db_file_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM email_logs")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0

def test_root_endpoint():
    response = client.get("/api")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Welcome" in data["message"]

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

@patch("fastapi_mail.FastMail.send_message", new_callable=AsyncMock)
def test_send_plain_email_success(mock_send):
    initial_count = get_db_log_count()
    payload = {
        "recipient": "recipient@example.com",
        "subject": "Hello Plain",
        "body": "This is a plain text body"
    }
    response = client.post("/send-email", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    mock_send.assert_called_once()
    assert get_db_log_count() == initial_count + 1

def test_send_plain_email_invalid_recipient():
    payload = {
        "recipient": "invalid-email-address",
        "subject": "Hello Plain",
        "body": "This is a plain text body"
    }
    response = client.post("/send-email", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert "recipient" in data["message"]

def test_send_plain_email_empty_subject():
    payload = {
        "recipient": "recipient@example.com",
        "subject": "  ",
        "body": "This is a plain text body"
    }
    response = client.post("/send-email", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert "subject" in data["message"]

@patch("fastapi_mail.FastMail.send_message", new_callable=AsyncMock)
def test_send_html_email_success(mock_send):
    payload = {
        "recipient": "recipient@example.com",
        "subject": "Hello HTML",
        "template_name": "welcome.html",
        "template_data": {
            "name": "John Doe",
            "company": "Acme Corp"
        }
    }
    response = client.post("/send-html-email", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    mock_send.assert_called_once()

def test_send_html_email_not_found_template():
    payload = {
        "recipient": "recipient@example.com",
        "subject": "Hello HTML",
        "template_name": "non_existent.html",
        "template_data": {}
    }
    response = client.post("/send-html-email", json=payload)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "non_existent.html" in data["message"]

@patch("fastapi_mail.FastMail.send_message", new_callable=AsyncMock)
def test_send_email_with_attachment_success(mock_send):
    file_content = b"This is a dummy text file content."
    file_name = "test_attachment.txt"
    files = {
        "file": (file_name, io.BytesIO(file_content), "text/plain")
    }
    data = {
        "recipient": "recipient@example.com",
        "subject": "Subject with attachment",
        "body": "Please see attached file."
    }
    response = client.post("/send-email-with-attachment", data=data, files=files)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    mock_send.assert_called_once()

def test_send_email_with_attachment_invalid_extension():
    file_content = b"This is a dummy exe file content."
    file_name = "malware.exe"
    files = {
        "file": (file_name, io.BytesIO(file_content), "application/octet-stream")
    }
    data = {
        "recipient": "recipient@example.com",
        "subject": "Subject with attachment",
        "body": "Please see attached file."
    }
    response = client.post("/send-email-with-attachment", data=data, files=files)
    assert response.status_code == 400
    res_data = response.json()
    assert res_data["success"] is False
    assert "not is not allowed" in res_data["message"] or "is not allowed" in res_data["message"]

def test_send_email_with_attachment_too_large():
    # 5MB + 1 byte
    large_content = b"x" * (5 * 1024 * 1024 + 1)
    file_name = "large.zip"
    files = {
        "file": (file_name, io.BytesIO(large_content), "application/zip")
    }
    data = {
        "recipient": "recipient@example.com",
        "subject": "Subject with attachment",
        "body": "Please see attached file."
    }
    response = client.post("/send-email-with-attachment", data=data, files=files)
    assert response.status_code == 400
    res_data = response.json()
    assert res_data["success"] is False
    assert "exceeds maximum limit" in res_data["message"]


def test_get_logs_endpoint():
    response = client.get("/api/logs")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "logs" in data
    assert isinstance(data["logs"], list)


def test_get_templates_list():
    response = client.get("/api/templates")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "templates" in data
    assert "welcome.html" in data["templates"]


def test_save_and_get_template():
    payload = {
        "name": "test_saved_template.html",
        "content": "<h1>Hello {{ name }}</h1>"
    }
    response = client.post("/api/templates", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    response = client.get("/api/templates/test_saved_template.html")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Hello {{ name }}" in data["content"]


@patch("fastapi_mail.FastMail.send_message", new_callable=AsyncMock)
def test_send_html_email_with_attachment_success(mock_send):
    file_content = b"Dummy attachment info"
    file_name = "doc.txt"
    files = {
        "file": (file_name, io.BytesIO(file_content), "text/plain")
    }
    data = {
        "recipient": "recipient@example.com",
        "subject": "HTML Templated Subject",
        "template_name": "welcome.html",
        "template_data_json": '{"name": "John", "company": "Co"}'
    }
    response = client.post("/send-html-email-with-attachment", data=data, files=files)
    assert response.status_code == 200
    assert response.json()["success"] is True
    mock_send.assert_called_once()


@patch("fastapi_mail.FastMail.send_message", new_callable=AsyncMock)
def test_send_bulk_email_plain_success(mock_send):
    initial_count = get_db_log_count()
    data = {
        "recipients": "user1@example.com, user2@example.com",
        "subject": "Bulk Plain Subject",
        "body": "Hello to all of you"
    }
    response = client.post("/send-bulk-email", data=data)
    assert response.status_code == 202
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["recipients_count"] == 2
    
    assert get_db_log_count() == initial_count + 2
    assert mock_send.call_count == 2


def test_get_bulk_templates_list():
    response = client.get("/api/bulk-templates")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "templates" in data
    assert "advertisement.html" in data["templates"]
    assert "newsletter.html" in data["templates"]


def test_save_and_get_bulk_template():
    payload = {
        "name": "test_saved_bulk_template.html",
        "content": "<h1>Hello Bulk {{ name }}</h1>"
    }
    response = client.post("/api/bulk-templates", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    response = client.get("/api/bulk-templates/test_saved_bulk_template.html")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Hello Bulk {{ name }}" in data["content"]


@patch("fastapi_mail.FastMail.send_message", new_callable=AsyncMock)
def test_send_bulk_email_templated_success(mock_send):
    initial_count = get_db_log_count()
    data = {
        "recipients": "user1@example.com, user2@example.com",
        "subject": "Bulk Templated Subject",
        "template_name": "advertisement.html",
        "template_data_json": '{"product_name": "Gadget X", "discount": "20%", "price": "$99", "description": "Awesome gadget", "cta_link": "http://x.com", "company_name": "Gadgets Inc"}'
    }
    response = client.post("/send-bulk-email", data=data)
    assert response.status_code == 202
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["recipients_count"] == 2
    
    assert get_db_log_count() == initial_count + 2
    assert mock_send.call_count == 2




