"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import engine, Base
from .routers import translation, glossary


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs" if settings.debug else None,
    )

    # CORS for Vite dev server
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Routes
    app.include_router(translation.router, prefix="/api/translation", tags=["translation"])
    app.include_router(glossary.router, prefix="/api/glossary", tags=["glossary"])

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "app": settings.app_name}

    return app


app = create_app()
