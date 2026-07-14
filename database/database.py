import os 
from sqlalchemy import event
from sqlmodel import create_engine, Session

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:password123@localhost:5432/veiculos"
)

engine = create_engine(DATABASE_URL, echo=True)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if engine.dialect.name == "sqlite":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

def get_session():
    """Injeta a sessão de banco de dados nas rotas"""
    with Session(engine) as session:
        yield session