from contextlib import asynccontextmanager

from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from app.auth.router import router as auth_router
from app.database import engine
from app.graphql.context import get_context
from app.graphql.schema import schema


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Las tablas ya existen en RDS — no las creamos aquí.
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="Tablo API", version="0.1.0", lifespan=lifespan)

    app.include_router(auth_router)

    graphql_app = GraphQLRouter(schema, context_getter=get_context)
    app.include_router(graphql_app, prefix="/graphql")

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
