"""
Main FastAPI application for Local AI Assistant
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from .config import settings, setup_logging, ensure_directories
from .models.init_db import initialize_database
from .utils.error_handler import APIException, ErrorHandler

# Import routes
from .routes import health, system, conversations, chat, models
from .routes import settings as settings_route

# Setup logging first so everything after it is captured
setup_logging(settings)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic"""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    try:
        ensure_directories(settings)
        initialize_database()
        logger.info("Application startup complete")
        yield
    except Exception as e:
        logger.critical(f"Fatal startup error: {e}")
        raise
    finally:
        logger.info("Application shutdown complete")


# Create app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Local AI Assistant — Privacy-focused offline AI chat",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None
)

# CORS — localhost only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{settings.port}",
        f"http://127.0.0.1:{settings.port}",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------
# Global exception handlers
# ------------------------------------------------------------------

@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    logger.warning(f"API exception [{exc.error_code}]: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "error_code": exc.error_code,
            "details": exc.details,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}")
    detail = exc.detail
    if isinstance(detail, dict):
        return JSONResponse(status_code=exc.status_code, content={
            **detail,
            "timestamp": datetime.utcnow().isoformat()
        })
    return JSONResponse(status_code=exc.status_code, content={
        "error": str(detail),
        "timestamp": datetime.utcnow().isoformat()
    })


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.warning(f"Validation error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Input validation failed",
            "details": exc.errors(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    error_id = ErrorHandler.log_error(exc, context=request.url.path, request=request)
    return JSONResponse(
        status_code=500,
        content={
            "error": "An unexpected error occurred",
            "error_id": error_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ------------------------------------------------------------------
# Routers
# ------------------------------------------------------------------

app.include_router(health.router,         prefix="/api", tags=["health"])
app.include_router(system.router,         prefix="/api", tags=["system"])
app.include_router(models.router,         prefix="/api", tags=["models"])
app.include_router(conversations.router,  prefix="/api", tags=["conversations"])
app.include_router(chat.router,           prefix="/api", tags=["chat"])
app.include_router(settings_route.router, prefix="/api", tags=["settings"])



# ------------------------------------------------------------------
# Static files + root route
# ------------------------------------------------------------------

frontend_dir = Path(__file__).parent.parent / "frontend"
css_file = frontend_dir / "css" / "style.css"


@app.get("/static/css/style.css", include_in_schema=False)
async def serve_css():
    if css_file.exists():
        return HTMLResponse(content=css_file.read_text(), media_type="text/css")
    return HTMLResponse("/* CSS not found */", status_code=404, media_type="text/css")


@app.get("/static/js/{filename}", include_in_schema=False)
async def serve_js(filename: str):
    js_file = frontend_dir / "js" / filename
    if js_file.exists():
        return FileResponse(str(js_file), media_type="application/javascript")
    return JSONResponse({"error": f"{filename} not found"}, status_code=404)


@app.get("/", include_in_schema=False)
async def root():
    index = frontend_dir / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "api_docs": "/docs",
        "mode": "local"
    }


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    raise HTTPException(status_code=404)


# ------------------------------------------------------------------
# Direct run
# ------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level=settings.log_level.lower()
    )
