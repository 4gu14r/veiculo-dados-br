# Dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instala ferramentas básicas para o banco de dados
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# AGORA APONTA DIRETAMENTE PARA O main.py NA RAIZ
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]