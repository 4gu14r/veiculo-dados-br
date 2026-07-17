# 🚗 Veículo Dados BR

API REST pública com especificações técnicas de veículos brasileiros.

[![CI](https://github.com/4gu14r/veiculo-dados-br/actions/workflows/ci.yml/badge.svg)](https://github.com/4gu14r/veiculo-dados-br/actions/workflows/ci.yml)

---

## Sobre

Dados de **89 marcas**, **832 modelos** e **5.687 versões** com fichas técnicas completas:
consumo, motor, dimensões, transmissão, suspensão e freios.

Os dados são atualizados automaticamente toda semana via scraping incremental do [FichaCompleta](http://fichacompleta.com.br/).

> ⚠️ Este projeto não possui vínculo oficial com nenhum fabricante ou fonte de dados. Uso informativo.

---

## Stack

| Camada | Tecnologia |
|---|---|
| API | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Banco | PostgreSQL 16 |
| Scraping | httpx + BeautifulSoup4 |
| Containers | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| Deploy | Render |

---

## Rodando localmente

### Pré-requisitos
- Docker e Docker Compose instalados

### 1. Clone e configure

```bash
git clone https://github.com/4gu14r/veiculo-dados-br.git
cd veiculo-dados-br

cp .env.example .env
# Edite o .env e defina um POSTGRES_PASSWORD
```

### 2. Suba os containers

```bash
docker compose up --build
```

API disponível em: http://localhost:8000

- **Swagger UI**: http://localhost:8000/docs
- **Redoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### 3. Importe os dados históricos (primeira vez apenas)

```bash
# Copie o banco SQLite legado para a pasta scripts/
cp /caminho/para/veiculos.db scripts/veiculos.db

# Execute o seed dentro do container
docker compose exec api python scripts/seed_from_sqlite.py /app/scripts/veiculos.db
```

---

## Endpoints

```
GET /health                            Health check

GET /api/v1/marcas                     Lista marcas (filtro: ?q=)
GET /api/v1/marcas/{id}                Detalhe da marca
GET /api/v1/marcas/{id}/modelos        Modelos de uma marca

GET /api/v1/modelos                    Lista modelos (filtro: ?q= ?marca_id=)
GET /api/v1/modelos/{id}               Detalhe do modelo
GET /api/v1/modelos/{id}/anos          Anos disponíveis do modelo

GET /api/v1/anos/{id}                  Detalhe do ano
GET /api/v1/anos/{id}/versoes          Versões de um modelo/ano

GET /api/v1/versoes                    Lista versões (filtro: ?ano= ?modelo_id=)
GET /api/v1/versoes/{id}               Ficha técnica completa
```

Todos os endpoints de listagem suportam `?pagina=1&limite=100`.

---

## Postman

Importe a collection direto pelo OpenAPI:

1. Abra o Postman → **Import**
2. Selecione **Link**
3. Cole: `https://seu-app.onrender.com/openapi.json`

---

## Estrutura do projeto

```
veiculo-dados-br/
├── main.py                        # Entrypoint — app factory
├── entrypoint.sh                  # Boot: migrations → uvicorn
├── Dockerfile                     # Build multi-stage
├── docker-compose.yml
├── alembic.ini
├── requirements.txt
├── render.yaml
├── api/
│   ├── core/
│   │   ├── config.py              # Settings via .env
│   │   └── database.py            # Engine e sessão
│   ├── models/
│   │   └── veiculo.py             # Marca, Modelo, ModeloAno, Versao, VersaoDetalhe
│   ├── schemas/
│   │   └── veiculo.py             # Schemas Pydantic (request/response)
│   ├── routers/
│   │   ├── marcas.py
│   │   ├── modelos.py
│   │   ├── anos.py
│   │   └── versoes.py
│   └── alembic/
│       └── versions/
│           └── 0001_initial.py
├── scraper/
│   ├── base.py                    # Classe base com HTTP client
│   ├── sources/
│   │   └── fichacompleta.py       # Scraper do fichacompleta.com.br
│   └── sync.py                    # Orquestra o scraping incremental
├── scripts/
│   └── seed_from_sqlite.py        # Migração única do banco legado
└── tests/
    ├── conftest.py
    └── test_api.py
```

---

## Deploy no Render

1. Conecte o repo no [Render](https://render.com)
2. Crie um Web Service → selecione **Docker**
3. Em **Environment Variables**, adicione:
   - `DATABASE_URL` → sua string de conexão do [Neon](https://neon.tech) ou [Supabase](https://supabase.com)
4. Deploy automático a cada push na `main`

---

## Desenvolvimento

```bash
# Testes
pytest tests/ -v

# Lint
ruff check .

# Rodar scraper manualmente
docker compose exec api python -m scraper.sync
```

---

## Licença

MIT
