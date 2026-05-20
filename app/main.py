"""Punto de entrada de la API REST de Tablo."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.routers import auth, projects, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verifica la conexión a la base de datos al arrancar.
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="API REST para Tablo, un clon de Trello (FastAPI + SQLAlchemy async).",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS abierto para desarrollo; restringir en producción.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(tasks.router)


@app.get("/health", tags=["health"], summary="Health check")
async def health() -> dict:
    return {"status": "ok", "service": settings.APP_NAME}
