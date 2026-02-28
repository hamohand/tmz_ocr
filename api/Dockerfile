FROM python:3.10-slim-bookworm

WORKDIR /app

# Installer Tesseract et ses dépendances
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements de l'API
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Créer les dossiers nécessaires
RUN mkdir -p /app/api /app/models

# Copier le code de l'API
COPY api /app/api
# Au build final, vous décommenterez cette ligne pour copier votre modèle
# COPY models/tmz_latn.traineddata /app/models/

ENV TESSDATA_PREFIX=/app/models

EXPOSE 8000

# Lancer FastAPI avec Uvicorn
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
