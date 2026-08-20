#!/bin/bash
set -e

GT_WSL="/home/hamoh/tmz_training/tesstrain/data/tmz_latn-ground-truth"
SYNTH="/mnt/c/Users/hamoh/Documents/travail/tmz/tmz_ocr/training/data/tmz_latn-ground-truth"
REAL="/mnt/c/Users/hamoh/Documents/travail/tmz/tmz_ocr/training/data/real-scans-gt"

echo "=== Étape 1/4 : Nettoyage ancien GT WSL ==="
find "$GT_WSL" -type f -delete 2>/dev/null || true
echo "   ✅ Nettoyé"

echo ""
echo "=== Étape 2/4 : Copie GT synthétique v5 ==="
cd "$SYNTH"
tar -cf - . | tar -xf - -C "$GT_WSL/"
SYNTH_COUNT=$(ls "$GT_WSL"/*.tif 2>/dev/null | wc -l)
echo "   ✅ $SYNTH_COUNT paires synthétiques copiées"

echo ""
echo "=== Étape 3/4 : Copie GT réel (vrais scans) ==="
cd "$REAL"
cp *.tif *.gt.txt "$GT_WSL/" 2>/dev/null || tar -cf - *.tif *.gt.txt | tar -xf - -C "$GT_WSL/"
echo "   ✅ GT réel copié"

echo ""
echo "=== Étape 4/4 : Statistiques finales ==="
TOTAL_TIF=$(ls "$GT_WSL"/*.tif | wc -l)
TOTAL_GT=$(ls "$GT_WSL"/*.gt.txt | wc -l)
echo "   🖼  $TOTAL_TIF fichiers .tif"
echo "   📝 $TOTAL_GT fichiers .gt.txt"

echo ""
echo "============================================================"
echo "✅ Prêt pour le training v5 !"
echo "   cd /home/hamoh/tmz_training/tesstrain"
echo "   make training MODEL_NAME=tmz_latn START_MODEL=tmz_latn \\"
echo "     TESSDATA=/home/hamoh/tmz_training/tesstrain/data/tessdata_best \\"
echo "     MAX_ITERATIONS=20000"
echo "============================================================"
