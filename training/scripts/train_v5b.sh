#!/bin/bash
set -e

GT_WSL="/home/hamoh/tmz_training/tesstrain/data/tmz_latn-ground-truth"
SYNTH="/mnt/c/Users/hamoh/Documents/travail/tmz/tmz_ocr/training/data/tmz_latn-ground-truth"
REAL="/mnt/c/Users/hamoh/Documents/travail/tmz/tmz_ocr/training/data/real-scans-gt"
TESSTRAIN="/home/hamoh/tmz_training/tesstrain"

echo "=== 1/5 : Nettoyage ancien GT + checkpoints ==="
find "$GT_WSL" -type f -delete 2>/dev/null || true
rm -rf "$TESSTRAIN/data/tmz_latn/checkpoints" 2>/dev/null || true
rm -f "$TESSTRAIN/data/tmz_latn"/*.lstmf 2>/dev/null || true
echo "   ✅ Nettoyé"

echo ""
echo "=== 2/5 : Copie GT synthétique v5 ==="
cd "$SYNTH"
tar -cf - . | tar -xf - -C "$GT_WSL/"
echo "   ✅ Copié"

echo ""
echo "=== 3/5 : Copie GT réel filtré (548 paires) ==="
cd "$REAL"
cp *.tif *.gt.txt "$GT_WSL/" 2>/dev/null || tar -cf - *.tif *.gt.txt | tar -xf - -C "$GT_WSL/"
echo "   ✅ Copié"

echo ""
echo "=== 4/5 : Statistiques ==="
TIF=$(find "$GT_WSL" -name "*.tif" | wc -l)
GT=$(find "$GT_WSL" -name "*.gt.txt" | wc -l)
echo "   🖼  $TIF fichiers .tif"
echo "   📝 $GT fichiers .gt.txt"

echo ""
echo "=== 5/5 : Lancement training v5b ==="
cd "$TESSTRAIN"
make training MODEL_NAME=tmz_latn START_MODEL=tmz_latn \
  TESSDATA="$TESSTRAIN/data/tessdata_best" \
  MAX_ITERATIONS=20000 2>&1 | tail -20
