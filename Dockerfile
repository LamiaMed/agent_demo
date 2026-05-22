FROM python:3.11-slim

WORKDIR /app

# Dépendances d'abord (cache Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir \
    -r requirements.txt

# Puis le code
COPY . .

# Variables d'env (surchargeables)
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Vérification santé automatique
HEALTHCHECK --interval=30s --timeout=5s \
    CMD curl -f http://localhost:8000/health \
    || exit 1

# Démarrage
CMD ["uvicorn", "app:app", \
    "--host", "0.0.0.0", \
    "--port", "8000"]
