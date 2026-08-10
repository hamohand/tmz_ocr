FROM python:3.11-slim-bookworm

WORKDIR /app

# Installer Tesseract et ses dépendances
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements et installer
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Créer les dossiers nécessaires
RUN mkdir -p /app/api/static /app/models

# Copier le modèle Tamazight
COPY models/tmz_latn.traineddata /app/models/

# Copier le code de l'API et le frontend
COPY api/ /app/api/

ENV TESSDATA_PREFIX=/app/models

EXPOSE 8000

# Lancer FastAPI avec Uvicorn
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
