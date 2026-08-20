#!/bin/bash
# prepare_v5.sh — Prépare l'entraînement v5
# Combine GT synthétiques v4 + GT réels (vrais scans corrigés) + support ʷ/ᵒ
set -e

WSL_TRAIN="/home/hamoh/tmz_training/tesstrain"
GT_DIR="$WSL_TRAIN/data/tmz_latn-ground-truth"
WIN_PROJECT="/mnt/c/Users/hamoh/Documents/travail/tmz/tmz_ocr"
REAL_SCANS="$WIN_PROJECT/training/data/real-scans-gt"

echo "============================================================"
echo "🚀 Préparation Training v5"
echo "============================================================"

# Étape 1 : Nettoyer l'ancien GT
echo ""
echo "📦 Étape 1/4 : Nettoyage de l'ancien GT..."
find "$GT_DIR" -name "*.tif" -delete 2>/dev/null || true
find "$GT_DIR" -name "*.gt.txt" -delete 2>/dev/null || true
find "$GT_DIR" -name "*.box" -delete 2>/dev/null || true
find "$GT_DIR" -name "*.lstmf" -delete 2>/dev/null || true
echo "   ✅ Ancien GT nettoyé"

# Étape 2 : Copier le GT réel (vrais scans) via tar pipe
echo ""
echo "📄 Étape 2/4 : Copie des GT réels (658 paires) vers WSL natif..."
REAL_COUNT=$(ls "$REAL_SCANS"/*.tif 2>/dev/null | wc -l)
echo "   Trouvé : $REAL_COUNT paires .tif dans $REAL_SCANS"

if [ "$REAL_COUNT" -gt 0 ]; then
    tar -cf - -C "$REAL_SCANS" --include='*.tif' --include='*.gt.txt' . 2>/dev/null | tar -xf - -C "$GT_DIR"
    echo "   ✅ GT réels copiés"
else
    echo "   ⚠️ Pas de fichiers .tif trouvés, copie fichier par fichier..."
    cp "$REAL_SCANS"/*.tif "$GT_DIR/" 2>/dev/null || true
    cp "$REAL_SCANS"/*.gt.txt "$GT_DIR/" 2>/dev/null || true
    echo "   ✅ GT réels copiés (méthode cp)"
fi

# Étape 3 : Régénérer le GT synthétique v4 (avec ʷ/ᵒ ajoutés au corpus)
echo ""
echo "🔄 Étape 3/4 : Génération du GT synthétique..."
cd "$WIN_PROJECT/training/scripts"

# Vérifier si ʷ et ᵒ sont dans le corpus v4
if grep -q 'ʷ' lignes_tamazight_v4.txt 2>/dev/null; then
    echo "   ✓ ʷ déjà présent dans le corpus"
else
    echo "   ⚠️ ʷ absent du corpus — ajout automatique non implémenté"
    echo "   → Ajoutez manuellement des mots avec ʷ au corpus avant de régénérer"
fi

# Générer le GT synthétique
echo "   Génération des images synthétiques..."
python3 generate_gt.py 2>&1 | tail -5

# Copier le GT synthétique via tar pipe
echo ""
echo "   Copie du GT synthétique vers WSL natif..."
SYNTH_DIR="$WIN_PROJECT/training/data/tmz_latn-ground-truth"
if [ -d "$SYNTH_DIR" ]; then
    tar -cf - -C "$SYNTH_DIR" . | tar -xf - -C "$GT_DIR"
    echo "   ✅ GT synthétique copié"
fi

# Compter le total
echo ""
echo "📊 Étape 4/4 : Statistiques finales"
TOTAL_TIF=$(ls "$GT_DIR"/*.tif 2>/dev/null | wc -l)
TOTAL_GT=$(ls "$GT_DIR"/*.gt.txt 2>/dev/null | wc -l)
echo "   🖼  $TOTAL_TIF fichiers .tif"
echo "   📝 $TOTAL_GT fichiers .gt.txt"

echo ""
echo "============================================================"
echo "✅ Prêt pour le training v5 !"
echo ""
echo "Lancez :"
echo "  cd $WSL_TRAIN"
echo "  make training MODEL_NAME=tmz_latn START_MODEL=tmz_latn \\"
echo "    TESSDATA=$WSL_TRAIN/data/tessdata_best \\"
echo "    MAX_ITERATIONS=20000"
echo "============================================================"
