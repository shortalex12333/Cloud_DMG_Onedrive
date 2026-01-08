"""FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

# Create FastAPI app
app = FastAPI(
    title="CelesteOS OneDrive Integration",
    description="Cloud-to-cloud document ingestion from OneDrive for Business",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
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
        "version": "0.1.0"
    }


# Import and include routers
from app.api.v1 import auth

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

# TODO: Add files and sync routers in Week 3
# from app.api.v1 import files, sync
# app.include_router(files.router, prefix="/api/v1/files", tags=["files"])
# app.include_router(sync.router, prefix="/api/v1/sync", tags=["sync"])
