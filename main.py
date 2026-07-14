# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import SQLModel

from database.database import engine
import api.models  

from api.routers.marcas import router as marcas_router
from api.routers.modelos import router as modelos_router
from api.routers.importacao import router as importacao_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Ligando API: Verificando e criando tabelas no PostgreSQL...")
    SQLModel.metadata.create_all(engine)
    yield
    print("Desligando API...")

app = FastAPI(
    title="Veículo Dados BR API",
    description="API para especificações de veículos",
    version="2.0.0",
    lifespan=lifespan
)

app.include_router(marcas_router)
app.include_router(modelos_router)
app.include_router(importacao_router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "mensagem": "API conectada ao Postgres e tabelas criadas com sucesso!"
    }