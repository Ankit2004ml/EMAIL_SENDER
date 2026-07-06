import os
import logging
import sqlite3
import json
from datetime import datetime
from app.config import settings

# Ensure logs directory exists
os.makedirs(settings.LOGS_DIR, exist_ok=True)
log_file_path = os.path.join(settings.LOGS_DIR, "email.log")
db_file_path = os.path.join(settings.LOGS_DIR, "email_history.db")

# Configure logger
logger = logging.getLogger("email_sender")
logger.setLevel(logging.INFO)

# File handler
file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
file_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(file_handler)

# Console handler for debugging
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
logger.addHandler(console_handler)

# Initialize SQLite Database
def init_db():
    try:
        conn = sqlite3.connect(db_file_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                recipient TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT,
                template_name TEXT,
                template_data TEXT,       -- JSON string of dynamic variables
                attachment_name TEXT,
                status TEXT NOT NULL,      -- 'SUCCESS' or 'FAILED'
                provider TEXT NOT NULL,
                response_time REAL,        -- Elapsed time in seconds
                error_message TEXT         -- Error description if failed
            );
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to initialize SQLite log database: {str(e)}")

init_db()

def log_success(
    recipient: str,
    subject: str,
    provider: str,
    elapsed_time: float,
    body: str = None,
    template_name: str = None,
    template_data: dict = None,
    attachment_name: str = None
):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Write to text file log
    log_message = (
        f"SUCCESS\n"
        f"{timestamp}\n"
        f"Sent To:\n"
        f"{recipient}\n"
        f"Subject:\n"
        f"{subject}\n"
        f"Provider:\n"
        f"{provider.upper()}\n"
        f"Time:\n"
        f"{elapsed_time:.2f} sec\n"
        f"{'-'*40}"
    )
    logger.info(log_message)

    # 2. Write to SQLite database
    try:
        conn = sqlite3.connect(db_file_path)
        cursor = conn.cursor()
        
        # Serialize template_data dict to JSON string if present
        template_data_json = json.dumps(template_data) if template_data is not None else None
        
        cursor.execute("""
            INSERT INTO email_logs 
            (recipient, subject, body, template_name, template_data, attachment_name, status, provider, response_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (recipient, subject, body, template_name, template_data_json, attachment_name, "SUCCESS", provider, elapsed_time))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to write success log to SQLite: {str(e)}")

def log_failed(
    recipient: str,
    reason: str,
    provider: str = "SMTP",
    subject: str = "",
    body: str = None,
    template_name: str = None,
    template_data: dict = None,
    attachment_name: str = None
):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Write to text file log
    log_message = (
        f"FAILED\n"
        f"{timestamp}\n"
        f"Recipient:\n"
        f"{recipient}\n"
        f"Reason:\n"
        f"{reason}\n"
        f"{'-'*40}"
    )
    logger.info(log_message)

    # 2. Write to SQLite database
    try:
        conn = sqlite3.connect(db_file_path)
        cursor = conn.cursor()
        
        # Serialize template_data dict to JSON string if present
        template_data_json = json.dumps(template_data) if template_data is not None else None
        
        cursor.execute("""
            INSERT INTO email_logs 
            (recipient, subject, body, template_name, template_data, attachment_name, status, provider, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (recipient, subject or "", body, template_name, template_data_json, attachment_name, "FAILED", provider, reason))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to write failure log to SQLite: {str(e)}")
