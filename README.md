# 📧 FastAPI Email Sender API

A production-ready Email Sending API built with **FastAPI** that supports SMTP email delivery, HTML templates, bulk emails, logging, and file uploads.

---

## 🚀 Features

- Send plain text emails
- Send HTML emails using Jinja2 templates
- Bulk email sending
- SMTP integration
- Email logging
- Template management
- File upload support
- RESTful API
- FastAPI automatic Swagger documentation
- Modular project architecture

---

# 🛠 Tech Stack

- Python 3.11+
- FastAPI
- FastAPI-Mail
- Jinja2
- Uvicorn
- Pydantic
- SMTP
- Python Logging

---

# 📂 Project Structure

```
EMAIL_SENDER/
│
├── app/
│   ├── api/
│   ├── bulk_templates/
│   ├── schemas/
│   ├── services/
│   │     └── email_service.py
│   ├── static/
│   ├── templates/
│   ├── utils/
│   ├── config.py
│   ├── logger.py
│   └── main.py
│
├── logs/
├── uploads/
├── tests/
│
├── .env
├── .env.template
├── requirements.txt
├── README.md
└── run.py
```

---

# ⚙ Installation

Clone the repository

```bash
git clone https://github.com/yourusername/email_sender.git
```

Move into the project

```bash
cd email_sender
```

Create Virtual Environment

Windows

```bash
python -m venv .venv
```

Activate

Windows

```bash
.venv\Scripts\activate
```

Linux/Mac

```bash
source .venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# 🔐 Environment Variables

Create a `.env` file.

Example

```env
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_FROM=your_email@gmail.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_STARTTLS=True
MAIL_SSL_TLS=False

SECRET_KEY=your_secret_key
```

---

# ▶ Running the Project

Using Python

```bash
python run.py
```

or

```bash
uvicorn app.main:app --reload
```

---

# 📖 API Documentation

Swagger UI

```
http://127.0.0.1:8000/docs
```

ReDoc

```
http://127.0.0.1:8000/redoc
```

---

# 📮 API Endpoints

## Send Email

```
POST /api/send-email
```

---

## Send HTML Email

```
POST /api/send-html-email
```

---

## Send Bulk Email

```
POST /api/bulk-email
```

---

## Upload Files

```
POST /api/upload
```

---

## Email Logs

```
GET /api/logs
```

---

## Available Templates

```
GET /api/templates
```

---

# 📝 Logging

Application logs are automatically stored inside the `logs/` directory.

Each email request records:

- Recipient
- Subject
- Status
- Timestamp
- SMTP Response
- Errors (if any)

---

# 🧪 Testing

Run tests using

```bash
pytest
```

---

# 📦 Requirements

Install all packages

```bash
pip install -r requirements.txt
```

---

# 🔒 Security

- SMTP credentials stored using environment variables
- Sensitive information excluded from version control
- Input validation using Pydantic schemas

---

# 👨‍💻 Author

**Ankit Maity**

GitHub:
https://github.com/yourusername

LinkedIn:
https://linkedin.com/in/yourprofile

---

# 📄 License

This project is licensed under the MIT License.

---

## ⭐ If you like this project, don't forget to give it a Star on GitHub!
