"""FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="CelesteOS OneDrive Integration",
    description="Cloud-to-cloud document ingestion from OneDrive for Business",
    version="0.1.1"  # Updated to force redeploy
)

# Log CORS configuration on startup
cors_origins = settings.cors_origins
logger.info(f"Configuring CORS with origins: {cors_origins}")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "CelesteOS OneDrive Integration",
        "version": "0.1.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "onedrive-integration",
        "version": "0.1.1"
    }


@app.get("/debug/cors")
async def debug_cors():
    """Debug endpoint to check CORS configuration"""
    return {
        "cors_origins": settings.cors_origins,
        "cors_origins_type": type(settings.cors_origins).__name__,
        "cors_origins_count": len(settings.cors_origins)
    }


# Import and include routers
from app.api.v1 import auth, files, sync

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(files.router, prefix="/api/v1/files", tags=["files"])
app.include_router(sync.router, prefix="/api/v1/sync", tags=["sync"])
