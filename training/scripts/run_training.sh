#!/bin/bash
set -e

PROJECT=/mnt/c/Users/hamoh/Documents/travail/tmz/tmz_ocr
TESSTRAIN=$PROJECT/training/tesstrain
GT_DIR=$PROJECT/training/data/tmz_latn-ground-truth
TESSDATA_BEST=$TESSTRAIN/data/tessdata_best

echo "=== Étape 1: Télécharger le modèle fra BEST (float) ==="
mkdir -p "$TESSDATA_BEST"
if [ -f "$TESSDATA_BEST/fra.traineddata" ]; then
    echo "[OK] fra.traineddata (best) déjà présent"
else
    echo "Téléchargement de fra.traineddata (best)..."
    wget -O "$TESSDATA_BEST/fra.traineddata" \
        https://github.com/tesseract-ocr/tessdata_best/raw/main/fra.traineddata
    echo "[OK] Téléchargé"
fi

echo ""
echo "=== Étape 2: Nettoyage des artefacts précédents ==="
rm -rf "$TESSTRAIN/data/fra" 2>/dev/null
rm -rf "$TESSTRAIN/data/tmz_latn/checkpoints" 2>/dev/null
rm -f "$TESSTRAIN/data/tmz_latn/tmz_latn.traineddata" 2>/dev/null
rm -f "$TESSTRAIN/data/tmz_latn/list.train" 2>/dev/null
rm -f "$TESSTRAIN/data/tmz_latn/list.eval" 2>/dev/null
rm -f "$TESSTRAIN/data/tmz_latn/all-lstmf" 2>/dev/null
echo "[OK] Nettoyé"

echo ""
echo "=== Étape 3: Lancement de l'entraînement ==="
echo "Modèle de base: fra (BEST/float)"
echo "Iterations max: 20000"
echo ""

cd "$TESSTRAIN"
make training MODEL_NAME=tmz_latn START_MODEL=fra TESSDATA=$TESSDATA_BEST MAX_ITERATIONS=20000
