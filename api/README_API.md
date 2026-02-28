# Démarrer l'API OCR Tamazight

Ce dossier contient une petite API autonome pour tester et utiliser votre modèle.

## En local (sans Docker)

1. Assurez-vous d'avoir Tesseract installé sur votre machine (`sudo apt install tesseract-ocr`).
2. Placez votre modèle final dans le dossier parent : `../models/tmz_latn.traineddata`.
3. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
4. Lancez le serveur :
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```
5. Testez l'API : Envoyez une requête POST sur `http://localhost:8000/ocr` avec un fichier nomé `file` contenant votre image.

## Avec Docker

1. Copiez d'abord votre modèle final dans le dossier `models/`.
2. Décommentez la ligne `COPY models/tmz_latn.traineddata /app/models/` dans le fichier `Dockerfile`.
3. Depuis la racine du projet (le dossier `tmz_ocr`), lancez la construction :
   ```bash
   docker build -t tamazight-ocr-api -f api/Dockerfile .
   ```
4. Lancez le conteneur :
   ```bash
   docker run -p 8000:8000 tamazight-ocr-api
   ```
