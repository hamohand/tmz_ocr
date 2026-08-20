#!/bin/bash
TIF=$(find /home/hamoh/tmz_training/tesstrain/data/tmz_latn-ground-truth -name "*.tif" | wc -l)
GT=$(find /home/hamoh/tmz_training/tesstrain/data/tmz_latn-ground-truth -name "*.gt.txt" | wc -l)
echo "🖼  $TIF fichiers .tif"
echo "📝 $GT fichiers .gt.txt"
echo "Total: $((TIF + GT)) fichiers"
