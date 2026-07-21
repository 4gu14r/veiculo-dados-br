from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.core.config import settings
from api.core.database import get_db  # Import da sua conexão com o banco
from api.routers import marcas, modelos, versoes


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

    @app.get("/", tags=["Health"], summary="Health check")
    def health(db: Session = Depends(get_db)):
        try:
            db.execute(text("SELECT 1"))
            return {"status": "ok", "version": "2.0.0", "database": "connected"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro de conexão com o banco de dados: {str(e)}",
            )

    app.include_router(marcas.router, prefix="/api/v1/marcas", tags=["Marcas"])
    app.include_router(modelos.router, prefix="/api/v1/modelos", tags=["Modelos"])
    app.include_router(versoes.router, prefix="/api/v1/versoes", tags=["Versões"])

    return app


app = create_app()
