#!/bin/bash
MODELS=/mnt/c/Users/hamoh/Documents/travail/tmz/tmz_ocr/models
GT=/mnt/c/Users/hamoh/Documents/travail/tmz/tmz_ocr/training/data/tmz_latn-ground-truth

echo "=== Test du modèle tmz_latn.traineddata ==="
echo ""

correct=0
total=0

for i in 0 1 2 5 10 50 100 500 1000 2000 3000 4000 4900; do
    idx=$(printf "%04d" $i)
    tif="$GT/tmz_latn_${idx}.tif"
    gt_file="$GT/tmz_latn_${idx}.gt.txt"

    if [ ! -f "$tif" ]; then continue; fi

    expected=$(cat "$gt_file")
    result=$(tesseract "$tif" stdout -l tmz_latn --tessdata-dir "$MODELS" 2>/dev/null | tr -d '\n\r')

    total=$((total+1))

    if [ "$result" = "$expected" ]; then
        status="✅"
        correct=$((correct+1))
    else
        status="❌"
    fi

    echo "$status [$idx]"
    echo "  Attendu:  $expected"
    echo "  Reconnu:  $result"
    echo ""
done

echo "=== Résultat: $correct/$total correct ==="
