"""
RecoveryAssistant - Main FastAPI Application

Automated receivables collection system with AI-powered communications.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import settings
from .api.v1 import receivables, customers, payments, analytics, webhooks

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Automated Receivables Collection System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "1.0.0",
    }


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "RecoveryAssistant API",
        "version": "1.0.0",
        "docs": "/docs",
    }


# Include API routers
app.include_router(
    receivables.router,
    prefix=f"{settings.API_V1_PREFIX}/receivables",
    tags=["Receivables"]
)

app.include_router(
    customers.router,
    prefix=f"{settings.API_V1_PREFIX}/customers",
    tags=["Customers"]
)

app.include_router(
    payments.router,
    prefix=f"{settings.API_V1_PREFIX}/payments",
    tags=["Payments"]
)

app.include_router(
    analytics.router,
    prefix=f"{settings.API_V1_PREFIX}/analytics",
    tags=["Analytics"]
)

app.include_router(
    webhooks.router,
    prefix=f"{settings.API_V1_PREFIX}/webhooks",
    tags=["Webhooks"]
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
