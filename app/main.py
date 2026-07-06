from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.email_routes import router as email_router
from app.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="A production-ready email sending service supporting plain text, HTML templates, and attachments.",
    version="1.0.0"
)

# Optional CORS middleware - enabled for safety
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(email_router)

# Custom Exception Handlers for standardizing API responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "error": "HTTPException"
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Format Pydantic errors into a readable message
    errors = exc.errors()
    error_messages = []
    for err in errors:
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "Unknown validation error")
        error_messages.append(f"{loc}: {msg}")
    
    combined_message = "; ".join(error_messages)
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": combined_message,
            "error": "ValidationError"
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": str(exc) or "An unexpected server error occurred.",
            "error": exc.__class__.__name__
        }
    )

# Mount static files at root for serving Web UI
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")

