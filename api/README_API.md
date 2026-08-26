# Démarrer l'API OCR Tamazight v4.0.0

Ce dossier contient une API autonome pour tester et utiliser votre modèle. Elle inclut 4 modes OCR :
- `hybride` (`fra` + `kab`)
- `tmz_only`
- `kab_only` (utilise le modèle de Bouaziz Ait Driss pour l'évaluation)
- `compare` (compare les résultats de `kab` et `kab`)

## En local (sans Docker)

1. Assurez-vous d'avoir Tesseract installé sur votre machine (`sudo apt install tesseract-ocr`).
2. Placez vos modèles (`kab_bouaziz.traineddata` et `kab_bouaziz.traineddata`) dans le dossier `../models/`.
3. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
4. Lancez le serveur avec le script fourni (qui prépare la variable `TESSDATA_PREFIX`) :
   ```bash
   ./start_api.sh
   ```
   *(Ou via `uvicorn app:app --host 0.0.0.0 --port 8000 --reload` si l'environnement est bien configuré).*
5. Testez l'API : Envoyez une requête POST sur `http://localhost:8000/ocr` avec un fichier nommé `file` contenant votre image, et paramétrez le champ `mode` (par exemple `mode=compare`).

## Avec Docker

1. Copiez d'abord vos modèles dans le dossier `models/`.
2. Assurez-vous que les lignes `COPY models/kab_bouaziz.traineddata /app/models/` et `COPY models/kab_bouaziz.traineddata /app/models/` sont actives dans le fichier `Dockerfile`.
3. Depuis la racine du projet (le dossier `tmz_ocr`), lancez la construction :
   ```bash
   docker build -t tamazight-ocr-api -f api/Dockerfile .
   ```
4. Lancez le conteneur :
   ```bash
   docker run -p 8000:8000 tamazight-ocr-api
   ```
