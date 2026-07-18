from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core.config import settings
from api.routers import marcas, modelos, scrape_erros, versoes


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Veículo Dados BR",
        description=(
            "API pública com especificações técnicas de veículos brasileiros.\n\n"
            "Dados de consumo, motor, dimensões, transmissão, suspensão e freios "
            "extraídos e mantidos atualizados via scraping."
        ),
        version="2.0.0",
        contact={
            "name": "GitHub",
            "url": "https://github.com/4gu14r/veiculo-dados-br",
        },
        license_info={"name": "MIT"},
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    app.include_router(marcas.router,       prefix="/api/v1/marcas",       tags=["Marcas"])
    app.include_router(modelos.router,      prefix="/api/v1/modelos",      tags=["Modelos"])
    app.include_router(versoes.router,      prefix="/api/v1/versoes",      tags=["Versões"])
    app.include_router(scrape_erros.router, prefix="/api/v1/scrape-erros", tags=["Scrape Erros"])

    @app.get("/health", tags=["Health"], summary="Health check")
    def health():
        return {"status": "ok", "version": "2.0.0"}

    return app


app = create_app()
