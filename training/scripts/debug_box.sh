#!/bin/bash
BOX_DIR=/mnt/c/Users/hamoh/Documents/travail/tmz/tmz_ocr/training/tesstrain/data/tmz_latn-ground-truth
GT_DIR=/mnt/c/Users/hamoh/Documents/travail/tmz/tmz_ocr/training/data/tmz_latn-ground-truth

echo "=== Box file content ==="
cat "$BOX_DIR/tmz_latn_0000.box" 2>/dev/null
echo ""
echo "=== Box file size ==="
wc -c "$BOX_DIR/tmz_latn_0000.box" 2>/dev/null || echo "FILE NOT FOUND"
echo ""
echo "=== GT text ==="
cat "$GT_DIR/tmz_latn_0000.gt.txt"
echo ""
echo "=== Image info ==="
python3 << 'PYEOF'
from PIL import Image
img = Image.open("/mnt/c/Users/hamoh/Documents/travail/tmz/tmz_ocr/training/data/tmz_latn-ground-truth/tmz_latn_0000.tif")
print(f"Size: {img.size}, Mode: {img.mode}")
PYEOF
