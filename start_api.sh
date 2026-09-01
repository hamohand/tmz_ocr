#!/bin/bash
# ── Lancement de l'API Tamazight OCR via WSL ──
set -e

PROJECT=/mnt/c/Users/hamoh/Documents/travail/tmz/tmz_ocr
MODELS=$PROJECT/models

# Vérifier que le modèle existe
# if [ ! -f "$MODELS/tmz_latn.traineddata" ]; then
#     echo "ERREUR: tmz_latn.traineddata non trouvé dans $MODELS"
#     exit 1
# fi

if [ ! -f "$MODELS/kab.traineddata" ]; then
    echo "ERREUR: kab.traineddata non trouvé dans $MODELS"
    exit 1
fi

export TESSDATA_PREFIX=$MODELS

# Installer les dépendances Python si nécessaire
pip3 install --user --break-system-packages fastapi uvicorn pytesseract Pillow python-multipart 2>/dev/null

echo ""
echo "  ⵣ  Tamazight OCR API"
echo "  ────────────────────"
echo "  Interface web : http://127.0.0.1:8000"
echo "  Documentation : http://127.0.0.1:8000/docs"
echo "  Santé API     : http://127.0.0.1:8000/api/health"
echo ""
echo "  Ctrl+C pour arrêter"
echo ""

cd "$PROJECT"
python3 -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
