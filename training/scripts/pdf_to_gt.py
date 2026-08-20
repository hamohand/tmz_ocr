#!/usr/bin/env python3
"""
pdf_to_gt.py — Convertit un PDF en paires Ground Truth pour l'entraînement Tesseract.

Pipeline :
  1. PDF → images haute résolution (300 DPI)
  2. Images → découpage en lignes via Tesseract
  3. OCR v4 pré-remplit le texte de chaque ligne
  4. L'utilisateur corrige les fichiers .gt.txt
  5. Les paires corrigées servent au training v5

Usage :
  python3 pdf_to_gt.py mon_livre.pdf [--pages 1-10] [--dpi 300] [--lang tmz_latn]

Sortie :
  output/mon_livre/
  ├── pages/          # Images des pages complètes
  ├── lines/          # Images des lignes découpées + .gt.txt pré-remplis
  ├── review.html     # Interface de revue (correction dans le navigateur)
  └── stats.json      # Statistiques d'extraction
"""
import os
import sys
import json
import argparse
from datetime import datetime

try:
    from pdf2image import convert_from_path
except ImportError:
    print("❌ pdf2image non installé. Exécutez : pip install pdf2image")
    sys.exit(1)

try:
    import pytesseract
    from PIL import Image
except ImportError:
    print("❌ pytesseract ou Pillow non installé.")
    sys.exit(1)

# Configuration
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models"))
os.environ["TESSDATA_PREFIX"] = MODELS_DIR

TMZ_SPECIAL = set("čḍǧḥɣṛṣṭẓɛţČḌǦḤƔṚṢṬẒƐŢ")


def split_page_columns(page_img, num_cols=2, trim_pct=0.02):
    """Découpe une page en colonnes (gauche/droite).
    trim_pct : pourcentage retiré au bord intérieur de la colonne gauche
               pour éviter de capturer le début de la colonne droite."""
    w = page_img.width
    h = page_img.height
    trim = int(w * trim_pct)
    mid = w // num_cols

    columns = [
        # Colonne gauche : du début jusqu'au milieu - trim (évite le débordement)
        (page_img.crop((0, 0, mid - trim, h)), 0),
        # Colonne droite : commence un peu avant le milieu (1%) pour ne rien couper
        (page_img.crop((mid - int(w * 0.01), 0, w, h)), mid - int(w * 0.01)),
    ]

    return columns


def pdf_to_images(pdf_path, dpi=300, pages=None):
    """Convertit un PDF en images haute résolution."""
    print(f"📄 Conversion PDF → images ({dpi} DPI)...")

    kwargs = {"dpi": dpi, "fmt": "png"}
    if pages:
        kwargs["first_page"] = pages[0]
        kwargs["last_page"] = pages[1]

    images = convert_from_path(pdf_path, **kwargs)
    print(f"   ✓ {len(images)} pages converties")
    return images


def extract_lines(page_img, page_num, lang="tmz_latn"):
    """Découpe une page en lignes et fait l'OCR sur chaque ligne."""
    # PSM 3 = segmentation automatique complète (gère paragraphes, colonnes, etc.)
    data = pytesseract.image_to_data(
        page_img, lang=lang, config="--psm 3",
        output_type=pytesseract.Output.DICT
    )

    lines = {}
    for i, text in enumerate(data["text"]):
        line_num = data["line_num"][i]
        block_num = data["block_num"][i]
        par_num = data["par_num"][i]
        key = (block_num, par_num, line_num)

        if key not in lines:
            lines[key] = {
                "words": [],
                "x_min": data["left"][i],
                "y_min": data["top"][i],
                "x_max": data["left"][i] + data["width"][i],
                "y_max": data["top"][i] + data["height"][i],
                "confs": [],
            }

        if text.strip():
            lines[key]["words"].append(text)
            lines[key]["confs"].append(data["conf"][i])

        # Étendre les bounding boxes
        lines[key]["x_min"] = min(lines[key]["x_min"], data["left"][i])
        lines[key]["y_min"] = min(lines[key]["y_min"], data["top"][i])
        lines[key]["x_max"] = max(lines[key]["x_max"], data["left"][i] + data["width"][i])
        lines[key]["y_max"] = max(lines[key]["y_max"], data["top"][i] + data["height"][i])

    # Filtrer les lignes vides et trop courtes, trier par position verticale (y)
    filtered = []
    for key, line in lines.items():
        text = " ".join(line["words"]).strip()
        if len(text) < 3:  # Ignorer les lignes trop courtes
            continue
        filtered.append((line["y_min"], key, line, text))

    # Tri par position verticale (haut → bas) pour l'ordre de lecture naturel
    filtered.sort(key=lambda x: x[0])

    result = []
    for y_min, key, line, text in filtered:
        avg_conf = sum(line["confs"]) / len(line["confs"]) if line["confs"] else 0

        # Marge autour de la ligne (5 pixels)
        margin = 5
        x1 = max(0, line["x_min"] - margin)
        y1 = max(0, line["y_min"] - margin)
        x2 = min(page_img.width, line["x_max"] + margin)
        y2 = min(page_img.height, line["y_max"] + margin)

        line_img = page_img.crop((x1, y1, x2, y2))

        result.append({
            "image": line_img,
            "text": text,
            "confidence": round(avg_conf, 1),
            "bbox": (x1, y1, x2, y2),
            "special_chars": sum(1 for c in text if c in TMZ_SPECIAL),
        })

    return result


def generate_review_html(output_dir, all_lines_info):
    """Génère une page HTML pour faciliter la correction humaine."""
    html = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Revue Ground Truth — Tamazight OCR</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Segoe UI', sans-serif; background: #1a1a2e; color: #e0e0e0; padding: 20px; }
  h1 { color: #e94560; margin-bottom: 10px; }
  .stats { color: #888; margin-bottom: 20px; }
  .line-pair {
    display: flex; align-items: center; gap: 16px;
    background: #16213e; border-radius: 8px; padding: 10px; margin: 6px 0;
    border-left: 3px solid #0f3460;
  }
  .line-pair:hover { border-left-color: #e94560; }
  .line-pair.low-conf { border-left-color: #e94560; background: #1a1020; }
  .line-pair img { max-height: 50px; border-radius: 4px; background: white; padding: 2px; }
  .line-pair input {
    flex: 1; font-size: 16px; padding: 8px 12px;
    background: #0f3460; color: #e0e0e0; border: 1px solid #333;
    border-radius: 6px; font-family: 'Noto Sans', sans-serif;
  }
  .line-pair input:focus { border-color: #e94560; outline: none; }
  .conf { font-size: 12px; color: #888; min-width: 50px; text-align: right; }
  .conf.low { color: #e94560; font-weight: bold; }
  .page-header { background: #0f3460; padding: 10px 16px; border-radius: 8px; margin: 20px 0 10px; }
  button {
    background: #e94560; color: white; border: none; padding: 12px 24px;
    border-radius: 8px; font-size: 16px; cursor: pointer; margin: 20px 0;
  }
  button:hover { background: #c23152; }
  .special { color: #53d769; }
  .instructions { background: #0f3460; padding: 16px; border-radius: 8px; margin-bottom: 20px; }
  .instructions li { margin: 4px 0; }
  .char-palette {
    position: sticky; top: 0; z-index: 100;
    background: #0a0a1a; padding: 10px 16px; border-radius: 0 0 8px 8px;
    border-bottom: 2px solid #e94560; margin-bottom: 16px;
    display: flex; flex-wrap: wrap; gap: 4px; align-items: center;
  }
  .char-palette span.label { color: #888; font-size: 12px; margin-right: 8px; }
  .char-btn {
    background: #16213e; color: #53d769; border: 1px solid #333;
    border-radius: 4px; padding: 6px 10px; font-size: 18px; cursor: pointer;
    font-family: 'Noto Sans', sans-serif; min-width: 36px; text-align: center;
  }
  .char-btn:hover { background: #e94560; color: white; border-color: #e94560; }
  .char-btn.sep { background: none; border: none; color: #333; cursor: default; padding: 0 4px; }
  .char-btn.sep:hover { background: none; color: #333; }
</style>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;700&display=swap" rel="stylesheet">
</head>
<body>
<h1>ⵣ Revue Ground Truth — Tamazight OCR</h1>

<div class="char-palette" id="charPalette">
  <span class="label">Minuscules :</span>
  <button class="char-btn" onclick="insertChar('č')">č</button>
  <button class="char-btn" onclick="insertChar('ḍ')">ḍ</button>
  <button class="char-btn" onclick="insertChar('ǧ')">ǧ</button>
  <button class="char-btn" onclick="insertChar('ḥ')">ḥ</button>
  <button class="char-btn" onclick="insertChar('ɣ')">ɣ</button>
  <button class="char-btn" onclick="insertChar('ṛ')">ṛ</button>
  <button class="char-btn" onclick="insertChar('ṣ')">ṣ</button>
  <button class="char-btn" onclick="insertChar('ṭ')">ṭ</button>
  <button class="char-btn" onclick="insertChar('ẓ')">ẓ</button>
  <button class="char-btn" onclick="insertChar('ɛ')">ɛ</button>
  <button class="char-btn" onclick="insertChar('ţ')">ţ</button>
  <span class="char-btn sep">│</span>
  <span class="label">Majuscules :</span>
  <button class="char-btn" onclick="insertChar('Č')">Č</button>
  <button class="char-btn" onclick="insertChar('Ḍ')">Ḍ</button>
  <button class="char-btn" onclick="insertChar('Ǧ')">Ǧ</button>
  <button class="char-btn" onclick="insertChar('Ḥ')">Ḥ</button>
  <button class="char-btn" onclick="insertChar('Ɣ')">Ɣ</button>
  <button class="char-btn" onclick="insertChar('Ṛ')">Ṛ</button>
  <button class="char-btn" onclick="insertChar('Ṣ')">Ṣ</button>
  <button class="char-btn" onclick="insertChar('Ṭ')">Ṭ</button>
  <button class="char-btn" onclick="insertChar('Ẓ')">Ẓ</button>
  <button class="char-btn" onclick="insertChar('Ɛ')">Ɛ</button>
  <button class="char-btn" onclick="insertChar('Ţ')">Ţ</button>
  <span class="char-btn sep">│</span>
  <span class="label">Labio-vél. :</span>
  <button class="char-btn" onclick="insertChar('ʷ')" style="color:#ff6b6b">ʷ</button>
  <button class="char-btn" onclick="insertChar('ᵒ')" style="color:#ff6b6b">ᵒ</button>
  <span class="char-btn sep">│</span>
  <span class="label">Puces :</span>
  <button class="char-btn" onclick="insertChar('•')" style="color:#6bc5ff">•</button>
  <button class="char-btn" onclick="insertChar('◦')" style="color:#6bc5ff">◦</button>
  <button class="char-btn" onclick="insertChar('▪')" style="color:#6bc5ff">▪</button>
  <button class="char-btn" onclick="insertChar('◆')" style="color:#6bc5ff">◆</button>
  <button class="char-btn" onclick="insertChar('▸')" style="color:#6bc5ff">▸</button>
  <button class="char-btn" onclick="insertChar('–')" style="color:#6bc5ff">–</button>
  <button class="char-btn" onclick="insertChar('—')" style="color:#6bc5ff">—</button>
</div>

<div class="instructions">
  <strong>Instructions :</strong>
  <ul>
    <li>🔍 Chaque ligne montre l'image originale et le texte OCR pré-rempli</li>
    <li>✏️ Corrigez le texte si nécessaire (les lignes rouges ont une faible confiance)</li>
    <li>🔤 Cliquez un caractère dans la palette pour l'insérer à la position du curseur</li>
    <li>💾 Cliquez "Sauvegarder" pour télécharger les corrections</li>
  </ul>
</div>
"""
    total_lines = 0
    total_low_conf = 0

    for page_num, lines in all_lines_info:
        html += f'<div class="page-header">📄 Page {page_num} — {len(lines)} lignes</div>\n'
        for i, line in enumerate(lines):
            conf = line["confidence"]
            is_low = conf < 80
            if is_low:
                total_low_conf += 1
            total_lines += 1

            css_class = "line-pair low-conf" if is_low else "line-pair"
            conf_class = "conf low" if is_low else "conf"
            filename = line["filename"]

            html += f'''<div class="{css_class}">
  <img src="lines/{filename}.png" alt="{filename}">
  <input type="text" id="{filename}" value="{line["text"].replace('"', '&quot;')}">
  <span class="{conf_class}">{conf}%</span>
</div>\n'''

    html += f"""
<div class="stats">{total_lines} lignes extraites — {total_low_conf} à faible confiance (< 80%)</div>
<button onclick="saveCorrections()">💾 Sauvegarder les corrections</button>

<script>
// Palette de caractères : mémorise le dernier champ actif
let lastFocusedInput = null;
document.addEventListener('focusin', e => {{
  if (e.target.tagName === 'INPUT' && e.target.type === 'text') lastFocusedInput = e.target;
}});

function insertChar(ch) {{
  if (!lastFocusedInput) {{
    // Si aucun champ n'est sélectionné, focus le premier
    lastFocusedInput = document.querySelector('input[type=text]');
  }}
  const input = lastFocusedInput;
  const start = input.selectionStart;
  const end = input.selectionEnd;
  const val = input.value;
  input.value = val.slice(0, start) + ch + val.slice(end);
  input.selectionStart = input.selectionEnd = start + ch.length;
  input.focus();
}}

function saveCorrections() {{
  let corrections = [];
  document.querySelectorAll('input[type=text]').forEach(input => {{
    corrections.push(input.id + '\\t' + input.value);
  }});
  const blob = new Blob([corrections.join('\\n')], {{type: 'text/plain'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'corrections.tsv';
  a.click();
}}
</script>
</body></html>"""

    html_path = os.path.join(output_dir, "review.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    return html_path


def main():
    parser = argparse.ArgumentParser(description="Convertir un PDF en Ground Truth pour Tesseract")
    parser.add_argument("pdf", help="Chemin vers le fichier PDF")
    parser.add_argument("--pages", type=str, default=None, help="Plage de pages (ex: 1-10)")
    parser.add_argument("--dpi", type=int, default=300, help="Résolution (défaut: 300)")
    parser.add_argument("--lang", type=str, default="tmz_latn", help="Modèle Tesseract (défaut: tmz_latn)")
    parser.add_argument("--output", type=str, default=None, help="Dossier de sortie")
    parser.add_argument("--split-columns", action="store_true", help="Découpe chaque page en 2 colonnes (pour lexiques)")
    args = parser.parse_args()

    if not os.path.exists(args.pdf):
        print(f"❌ Fichier non trouvé : {args.pdf}")
        sys.exit(1)

    # Préparer les dossiers
    pdf_name = os.path.splitext(os.path.basename(args.pdf))[0]
    output_dir = args.output or os.path.join("output", pdf_name)
    pages_dir = os.path.join(output_dir, "pages")
    lines_dir = os.path.join(output_dir, "lines")
    os.makedirs(pages_dir, exist_ok=True)
    os.makedirs(lines_dir, exist_ok=True)

    print("=" * 60)
    print(f"📚 PDF → Ground Truth : {os.path.basename(args.pdf)}")
    print(f"   DPI: {args.dpi}, Modèle: {args.lang}")
    if args.split_columns:
        print(f"   📐 Mode 2 colonnes activé")
    print("=" * 60)

    # Plage de pages
    page_range = None
    if args.pages:
        parts = args.pages.split("-")
        if len(parts) == 1:
            page_range = (int(parts[0]), int(parts[0]))
        else:
            page_range = (int(parts[0]), int(parts[1]))
        print(f"   Pages : {page_range[0]} à {page_range[1]}")

    # 1. PDF → Images
    page_images = pdf_to_images(args.pdf, dpi=args.dpi, pages=page_range)

    # 2-3. Pour chaque page : découper en lignes + OCR
    all_lines_info = []
    total_lines = 0
    total_special = 0
    line_counter = 0

    for page_idx, page_img in enumerate(page_images):
        page_num = page_idx + 1 + (page_range[0] - 1 if page_range else 0)
        print(f"\n📄 Page {page_num} ({page_img.width}x{page_img.height})...")

        # Sauvegarder l'image de la page complète
        page_path = os.path.join(pages_dir, f"page_{page_num:03d}.png")
        page_img.save(page_path)

        # Extraire les lignes (avec ou sans découpe en colonnes)
        if args.split_columns:
            columns = split_page_columns(page_img)
            lines = []
            for col_idx, (col_img, x_offset) in enumerate(columns):
                col_label = "gauche" if col_idx == 0 else "droite"
                col_lines = extract_lines(col_img, page_num, lang=args.lang)
                # Recaler les bbox sur la page complète
                for cl in col_lines:
                    x1, y1, x2, y2 = cl["bbox"]
                    cl["bbox"] = (x1 + x_offset, y1, x2 + x_offset, y2)
                lines.extend(col_lines)
                print(f"   📐 Colonne {col_label} : {len(col_lines)} lignes")
        else:
            lines = extract_lines(page_img, page_num, lang=args.lang)
        print(f"   → {len(lines)} lignes extraites au total")

        page_lines = []
        for line in lines:
            filename = f"line_{page_num:03d}_{line_counter:05d}"

            # Sauvegarder l'image de la ligne
            line_img_path = os.path.join(lines_dir, f"{filename}.png")
            line["image"].save(line_img_path)

            # Sauvegarder aussi en .tif pour Tesseract
            tif_path = os.path.join(lines_dir, f"{filename}.tif")
            line["image"].save(tif_path)

            # Sauvegarder le texte OCR (à corriger par l'humain)
            gt_path = os.path.join(lines_dir, f"{filename}.gt.txt")
            with open(gt_path, "w", encoding="utf-8") as f:
                f.write(line["text"])

            page_lines.append({
                "filename": filename,
                "text": line["text"],
                "confidence": line["confidence"],
                "special_chars": line["special_chars"],
            })

            total_special += line["special_chars"]
            line_counter += 1

        all_lines_info.append((page_num, page_lines))
        total_lines += len(lines)

        # Aperçu des premières lignes
        for line in page_lines[:3]:
            conf_icon = "✅" if line["confidence"] >= 80 else "⚠️"
            print(f"   {conf_icon} [{line['confidence']}%] {line['text'][:70]}")

    # 4. Générer la page de revue HTML
    html_path = generate_review_html(output_dir, all_lines_info)

    # 5. Statistiques
    stats = {
        "pdf": os.path.basename(args.pdf),
        "date": datetime.now().isoformat(),
        "dpi": args.dpi,
        "lang": args.lang,
        "pages": len(page_images),
        "total_lines": total_lines,
        "total_special_chars": total_special,
    }
    stats_path = os.path.join(output_dir, "stats.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    # Résumé
    print("\n" + "=" * 60)
    print(f"✅ Extraction terminée !")
    print(f"   📄 {len(page_images)} pages → {total_lines} lignes")
    print(f"   🔤 {total_special} caractères spéciaux détectés")
    print(f"   📁 Sortie : {output_dir}/")
    print(f"   🌐 Revue  : {html_path}")
    print(f"\n📝 Étapes suivantes :")
    print(f"   1. Ouvrez {html_path} dans votre navigateur")
    print(f"   2. Corrigez les textes pré-remplis (surtout les lignes rouges)")
    print(f"   3. Sauvegardez les corrections")
    print(f"   4. Lancez : python3 apply_corrections.py {output_dir}/")
    print(f"   5. Les paires corrigées sont prêtes pour le training v5 !")


if __name__ == "__main__":
    main()
