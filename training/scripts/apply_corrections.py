#!/usr/bin/env python3
"""
apply_corrections.py — Applique les corrections des fichiers .tsv aux fichiers .gt.txt

Usage :
  python3 apply_corrections.py [--output-dir DOSSIER_FINAL]

Le script :
  1. Cherche tous les .tsv dans output/
  2. Pour chaque ligne du .tsv, met à jour le .gt.txt correspondant
  3. Copie les paires corrigées (.tif + .gt.txt) dans un dossier final
  4. Affiche les statistiques (lignes modifiées, caractères spéciaux, etc.)
"""
import os
import sys
import shutil
import glob

TMZ_SPECIAL = set("čḍǧḥɣṛṣṭẓɛţČḌǦḤƔṚṢṬẒƐŢʷᵒ")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
FINAL_DIR = os.path.join(SCRIPT_DIR, "..", "data", "real-scans-gt")


def find_lines_dir(tsv_path):
    """Trouve le dossier lines/ correspondant au fichier .tsv."""
    # Le .tsv est soit dans le même dossier que lines/, soit au même niveau que le dossier parent
    tsv_dir = os.path.dirname(tsv_path)
    tsv_name = os.path.splitext(os.path.basename(tsv_path))[0]

    # Cas 1 : output/document/lines/ et output/document/document.tsv
    lines_in_same = os.path.join(tsv_dir, "lines")
    if os.path.isdir(lines_in_same):
        return lines_in_same

    # Cas 2 : output/document.tsv et output/document/lines/
    lines_in_subdir = os.path.join(tsv_dir, tsv_name, "lines")
    if os.path.isdir(lines_in_subdir):
        return lines_in_subdir

    # Cas 3 : chercher un dossier avec un nom similaire
    for d in os.listdir(tsv_dir):
        candidate = os.path.join(tsv_dir, d, "lines")
        if os.path.isdir(candidate) and tsv_name.startswith(d[:20]):
            return candidate

    return None


def apply_tsv(tsv_path, final_dir):
    """Applique les corrections d'un .tsv et copie les paires corrigées."""
    lines_dir = find_lines_dir(tsv_path)
    if not lines_dir:
        print(f"  ⚠️  Dossier lines/ non trouvé pour {os.path.basename(tsv_path)}")
        return 0, 0, 0

    doc_name = os.path.splitext(os.path.basename(tsv_path))[0]
    print(f"\n📄 {doc_name}")
    print(f"   TSV : {tsv_path}")
    print(f"   Lines: {lines_dir}")

    total = 0
    modified = 0
    special_count = 0
    skipped = 0

    with open(tsv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n").rstrip("\r")
            if not line or "\t" not in line:
                continue

            parts = line.split("\t", 1)
            if len(parts) != 2:
                continue

            filename, corrected_text = parts
            corrected_text = corrected_text.strip()

            if not corrected_text:
                skipped += 1
                continue

            # Fichiers source
            gt_path = os.path.join(lines_dir, f"{filename}.gt.txt")
            tif_path = os.path.join(lines_dir, f"{filename}.tif")
            png_path = os.path.join(lines_dir, f"{filename}.png")

            if not os.path.exists(tif_path) and not os.path.exists(png_path):
                skipped += 1
                continue

            # Lire le texte OCR original
            original_text = ""
            if os.path.exists(gt_path):
                with open(gt_path, "r", encoding="utf-8") as gf:
                    original_text = gf.read().strip()

            # Vérifier si modifié
            was_modified = original_text != corrected_text

            # Mettre à jour le .gt.txt
            with open(gt_path, "w", encoding="utf-8") as gf:
                gf.write(corrected_text)

            # Copier vers le dossier final
            # Préfixer avec le nom du document pour éviter les collisions
            final_name = f"{doc_name}_{filename}"

            # Copier le .tif (ou convertir le .png en .tif)
            if os.path.exists(tif_path):
                shutil.copy2(tif_path, os.path.join(final_dir, f"{final_name}.tif"))
            elif os.path.exists(png_path):
                # Copier le PNG comme source (on pourra convertir plus tard)
                shutil.copy2(png_path, os.path.join(final_dir, f"{final_name}.png"))

            # Copier le .gt.txt corrigé
            shutil.copy2(gt_path, os.path.join(final_dir, f"{final_name}.gt.txt"))

            total += 1
            if was_modified:
                modified += 1
            special_count += sum(1 for c in corrected_text if c in TMZ_SPECIAL)

    print(f"   ✅ {total} lignes traitées, {modified} modifiées, {skipped} ignorées")
    print(f"   🔤 {special_count} caractères spéciaux")

    return total, modified, special_count


def convert_png_to_tif(final_dir):
    """Convertit les .png en .tif dans le dossier final (Tesseract préfère .tif)."""
    try:
        from PIL import Image
    except ImportError:
        print("⚠️  Pillow non installé, conversion PNG→TIF ignorée")
        return

    png_files = glob.glob(os.path.join(final_dir, "*.png"))
    converted = 0
    for png_path in png_files:
        tif_path = png_path.replace(".png", ".tif")
        if not os.path.exists(tif_path):
            img = Image.open(png_path)
            img.save(tif_path)
            converted += 1

    if converted:
        print(f"\n🔄 {converted} fichiers PNG convertis en TIF")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Appliquer les corrections TSV aux GT")
    parser.add_argument("--output-dir", type=str, default=FINAL_DIR,
                        help=f"Dossier de sortie final (défaut: {FINAL_DIR})")
    args = parser.parse_args()

    final_dir = args.output_dir
    os.makedirs(final_dir, exist_ok=True)

    print("=" * 60)
    print("📝 Application des corrections GT")
    print(f"   Source : {OUTPUT_DIR}")
    print(f"   Destination : {final_dir}")
    print("=" * 60)

    # Trouver tous les .tsv
    tsv_files = glob.glob(os.path.join(OUTPUT_DIR, "*.tsv"))
    tsv_files += glob.glob(os.path.join(OUTPUT_DIR, "*", "*.tsv"))
    # Dédupliquer
    tsv_files = list(set(tsv_files))
    tsv_files.sort()

    if not tsv_files:
        print("❌ Aucun fichier .tsv trouvé dans output/")
        sys.exit(1)

    print(f"\n📋 {len(tsv_files)} fichiers TSV trouvés")

    grand_total = 0
    grand_modified = 0
    grand_special = 0

    for tsv_path in tsv_files:
        total, modified, special = apply_tsv(tsv_path, final_dir)
        grand_total += total
        grand_modified += modified
        grand_special += special

    # Convertir PNG → TIF
    convert_png_to_tif(final_dir)

    # Statistiques finales
    gt_files = glob.glob(os.path.join(final_dir, "*.gt.txt"))
    tif_files = glob.glob(os.path.join(final_dir, "*.tif"))

    print("\n" + "=" * 60)
    print("✅ Corrections appliquées !")
    print(f"   📄 {grand_total} lignes traitées ({grand_modified} modifiées)")
    print(f"   🔤 {grand_special} caractères spéciaux au total")
    print(f"   📁 {len(gt_files)} fichiers .gt.txt dans {final_dir}")
    print(f"   🖼  {len(tif_files)} fichiers .tif dans {final_dir}")
    print(f"\n🚀 Prochaine étape :")
    print(f"   Ces paires GT sont prêtes pour le training v5 !")
    print(f"   Copiez-les dans le dossier GT principal ou combinez-les")
    print(f"   avec les GT synthétiques pour l'entraînement.")


if __name__ == "__main__":
    main()
