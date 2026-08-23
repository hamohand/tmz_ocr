"""
Tamazight OCR API — API dédiée à la reconnaissance de texte Tamazight Latin
Modèles disponibles :
  - tmz_latn.traineddata : notre modèle v5 (BCER 1.271%, 23 607 GT dont 548 vrais scans, wordlist 78K, support ʷ/ᵒ)
  - kab.traineddata : modèle Kabyle de Bouaziz Ait Driss (BCER 2.9%, 26 000 itérations)

Modes OCR :
  - hybrid : combine fra + tmz_latn (recommandé)
  - tmz_only : tmz_latn seul
  - kab_only : kab seul
  - compare : exécute tmz_latn ET kab côte à côte pour comparer
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pytesseract
from PIL import Image, ImageFilter, ImageEnhance
import io
import os
import json
import tempfile
import difflib
from datetime import datetime
from typing import Optional, List

try:
    from pdf2image import convert_from_bytes
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False

try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

# ── Configuration ──────────────────────────────────────────────
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))
os.environ["TESSDATA_PREFIX"] = MODELS_DIR

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# ── App FastAPI ────────────────────────────────────────────────
app = FastAPI(
    title="ⵣ Tamazight OCR API",
    description="API de reconnaissance optique de caractères pour le Tamazight Latin (Kabyle). Modèles : tmz_latn + kab (Bouaziz).",
    version="6.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Prétraitement d'image ─────────────────────────────────────
def preprocess_image(image: Image.Image, mode: str = "auto") -> Image.Image:
    """Prétraite l'image pour améliorer la qualité OCR."""
    # Convertir en niveaux de gris
    img = image.convert("L")

    if mode == "raw":
        return img

    # Agrandir si l'image est petite, en respectant le ratio
    w, h = img.size
    min_dim = min(w, h)
    if min_dim < 300:
        scale = 300 / min_dim
        # Limiter le redimensionnement pour ne pas créer d'images énormes
        scale = min(scale, 4.0)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    # Améliorer le contraste
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)

    # Améliorer la netteté
    img = img.filter(ImageFilter.SHARPEN)

    if mode == "binarize":
        # Binarisation (seuil adaptatif)
        img = img.point(lambda x: 0 if x < 140 else 255, '1')

    return img


def split_image_columns(image: Image.Image, num_cols: int = 2, trim_pct: float = 0.03) -> list:
    """Découpe une image en colonnes en détectant automatiquement la gouttière.
    Rogne les marges (haut, bas, côtés) pour ne garder que le texte."""
    import numpy as np

    w, h = image.size

    # 1. Rogner les marges extérieures (en-tête, pied de page, marges latérales)
    margin_top = int(h * 0.05)
    margin_bottom = int(h * 0.05)
    margin_left = int(w * 0.03)
    margin_right = int(w * 0.03)
    image = image.crop((margin_left, margin_top, w - margin_right, h - margin_bottom))
    w, h = image.size

    # 2. Convertir en niveaux de gris
    gray = image.convert("L")
    pixels = np.array(gray)

    # 3. Chercher la gouttière : bande la plus blanche dans le tiers central
    search_start = int(w * 0.35)
    search_end = int(w * 0.65)

    # Fenêtre glissante de 7 pixels pour robustesse
    window = 7
    trim = int(w * trim_pct)
    best_score = -1
    gutter = w // 2

    for x in range(search_start, search_end - window):
        score = pixels[:, x:x+window].mean()
        if score > best_score:
            best_score = score
            gutter = x + window // 2

    # 4. Découper les deux colonnes
    columns = [
        image.crop((0, 0, gutter - trim, h)),
        image.crop((gutter + trim, 0, w, h)),
    ]
    return columns


def auto_detect_psm(image: Image.Image, user_psm: int = 3) -> int:
    """
    Détecte automatiquement le meilleur PSM si l'utilisateur n'a pas choisi.
    
    - Image très haute et étroite (ratio > 2) → PSM 4 (colonne unique)
    - Image large → PSM 3 (auto)
    - L'utilisateur peut toujours forcer un PSM spécifique
    """
    if user_psm != 3:
        # L'utilisateur a choisi un PSM spécifique, le respecter
        return user_psm
    
    w, h = image.size
    ratio = h / w if w > 0 else 1
    
    if ratio > 2.0:
        # Image type colonne (haute et étroite) → PSM 4
        return 4
    
    return 3



# ── Caractères spécifiques Tamazight ───────────────────────────

# Table de normalisation : caractères visuellement identiques → forme standard tamazight
TMZ_NORMALIZE = {
    "\u03B5": "\u025B",  # ε epsilon grec → ɛ latin open e
    "\u0190": "\u0190",  # Ɛ (déjà correct, Latin capital open E)
    "\u0194": "\u0194",  # Ɣ (déjà correct, Latin capital Gamma)
}

def normalize_tmz(text: str) -> str:
    """Normalise les caractères confusables vers leur forme standard tamazight."""
    for src, dst in TMZ_NORMALIZE.items():
        text = text.replace(src, dst)
    return text

# Minuscules + majuscules : chaque lettre est indépendante (pas de lien maj/min en tamazight)
TMZ_SPECIAL_CHARS = set(
    "ḍṭṣẓṛḥɛɣčğţʷᵒ"   # minuscules
    "ḌṬṢẒṚḤƐƔČǦŢ"     # majuscules (Ẓ ≠ ẓ, Ḍ ≠ ḍ, etc.)
    "ƐƔŢ"               # variantes Unicode alternatives
)

def has_tamazight_chars(word: str) -> bool:
    """Vérifie si un mot contient des caractères spécifiques au Tamazight."""
    return any(c in TMZ_SPECIAL_CHARS for c in word)


def count_special_chars(text: str) -> dict:
    """Compte les caractères spéciaux tamazight dans un texte.
    Retourne le détail par caractère et le total."""
    char_counts = {}
    for c in text:
        if c in TMZ_SPECIAL_CHARS:
            char_counts[c] = char_counts.get(c, 0) + 1
    total = sum(char_counts.values())
    # Compter les mots contenant au moins un caractère spécial
    words_with_special = [w for w in text.split() if has_tamazight_chars(w)]
    return {
        "total_chars": total,
        "total_words": len(words_with_special),
        "detail": dict(sorted(char_counts.items(), key=lambda x: -x[1])),
    }


def hybrid_ocr(image, config: str = "--psm 3") -> dict:
    """
    OCR hybride intelligent :
    1. Lancer tmz_latn → verrouiller les mots avec caractères spéciaux
    2. Lancer fra → substituer les mots SANS caractères spéciaux si fra a une meilleure confiance
    Matching par position spatiale (block, par, ligne, position x).
    """
    # 1. Passe tmz_latn (primaire)
    data_tmz = pytesseract.image_to_data(
        image, lang="tmz_latn", config=config, output_type=pytesseract.Output.DICT
    )

    # 2. Passe fra (secondaire)
    try:
        data_fra = pytesseract.image_to_data(
            image, lang="fra", config=config, output_type=pytesseract.Output.DICT
        )
        has_fra = True
    except pytesseract.TesseractError:
        data_fra = None
        has_fra = False

    # 3. Construire l'index spatial fra : {(block, par, line): [(x, word, conf), ...]}
    fra_lines = {}
    if has_fra and data_fra:
        for i in range(len(data_fra["text"])):
            word = data_fra["text"][i].strip()
            if not word:
                continue
            key = (data_fra["block_num"][i], data_fra["par_num"][i], data_fra["line_num"][i])
            if key not in fra_lines:
                fra_lines[key] = []
            fra_lines[key].append({
                "word": word,
                "conf": data_fra["conf"][i],
                "x": data_fra["left"][i],
                "w": data_fra["width"][i],
            })

    # 4. Parcourir tmz_latn et substituer si pertinent
    words_result = []
    lines = {}

    for i in range(len(data_tmz["text"])):
        word_tmz = data_tmz["text"][i].strip()
        if not word_tmz:
            continue

        conf_tmz = data_tmz["conf"][i]
        block = data_tmz["block_num"][i]
        par = data_tmz["par_num"][i]
        line_num = data_tmz["line_num"][i]
        x_tmz = data_tmz["left"][i]
        w_tmz = data_tmz["width"][i]

        chosen_word = word_tmz
        chosen_conf = conf_tmz
        chosen_source = "tmz_latn"

        if has_tamazight_chars(word_tmz):
            # 🔒 Verrouillé : contient des caractères spéciaux → garder tmz_latn
            chosen_source = "tmz_latn🔒"
        elif has_fra and fra_lines:
            # Chercher le mot fra correspondant par position spatiale
            key = (block, par, line_num)
            if key in fra_lines:
                best_match = None
                best_overlap = 0
                cx_tmz = x_tmz + w_tmz / 2  # centre x du mot tmz

                for fra_word in fra_lines[key]:
                    cx_fra = fra_word["x"] + fra_word["w"] / 2
                    # Overlap = proximité des centres (en pixels)
                    distance = abs(cx_tmz - cx_fra)
                    max_w = max(w_tmz, fra_word["w"])
                    if max_w > 0 and distance < max_w * 0.6:
                        overlap = 1 - (distance / max_w)
                        if overlap > best_overlap:
                            best_overlap = overlap
                            best_match = fra_word

                if best_match and best_match["conf"] > conf_tmz and best_match["conf"] > 0:
                    chosen_word = best_match["word"]
                    chosen_conf = best_match["conf"]
                    chosen_source = "fra"

        key = (block, par, line_num)
        if key not in lines:
            lines[key] = []
        lines[key].append(chosen_word)

        words_result.append({
            "text": chosen_word,
            "confidence": chosen_conf,
            "source": chosen_source,
            "x": data_tmz["left"][i],
            "y": data_tmz["top"][i],
            "w": data_tmz["width"][i],
            "h": data_tmz["height"][i],
        })

    # Reconstruire le texte ligne par ligne (avec normalisation)
    text_lines = []
    for key in sorted(lines.keys()):
        text_lines.append(" ".join(lines[key]))
    final_text = normalize_tmz("\n".join(text_lines))

    # Normaliser aussi les mots individuels pour le comptage
    for w in words_result:
        w["text"] = normalize_tmz(w["text"])

    # Confiance globale et confiance sur les caractères spéciaux
    all_confs = [w["confidence"] for w in words_result if w["confidence"] > 0]
    special_confs = [w["confidence"] for w in words_result if w["confidence"] > 0 and has_tamazight_chars(w["text"])]
    special_words = [w["text"] for w in words_result if has_tamazight_chars(w["text"])]

    # Statistiques sources
    sources = {}
    for w in words_result:
        s = w["source"]
        sources[s] = sources.get(s, 0) + 1

    return {
        "text": final_text,
        "words": words_result,
        "sources": sources,
        "avg_confidence": round(sum(all_confs) / len(all_confs), 1) if all_confs else 0,
        "special_confidence": round(sum(special_confs) / len(special_confs), 1) if special_confs else 0,
        "special_count": len(special_words),
        "special_detail": count_special_chars(final_text),
    }


# ── Routes API ─────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Sert la page web du frontend."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>ⵣ Tamazight OCR API</h1><p>Frontend non trouvé. Utilisez POST /api/ocr</p>")


@app.get("/api/health")
async def health_check():
    """Vérifie que l'API et le modèle sont fonctionnels."""
    model_path = os.path.join(MODELS_DIR, "tmz_latn.traineddata")
    model_exists = os.path.exists(model_path)
    model_size = os.path.getsize(model_path) if model_exists else 0

    kab_path = os.path.join(MODELS_DIR, "kab.traineddata")
    kab_exists = os.path.exists(kab_path)
    kab_size = os.path.getsize(kab_path) if kab_exists else 0

    try:
        tesseract_version = pytesseract.get_tesseract_version()
    except Exception:
        tesseract_version = "non disponible"

    return {
        "status": "ok" if model_exists else "error",
        "models": {
            "tmz_latn": {
                "exists": model_exists,
                "size_mb": round(model_size / 1024 / 1024, 2),
            },
            "kab": {
                "exists": kab_exists,
                "size_mb": round(kab_size / 1024 / 1024, 2),
                "source": "Bouaziz Ait Driss (GitHub)",
            },
        },
        "tesseract_version": str(tesseract_version),
        "tessdata_prefix": MODELS_DIR,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/api/ocr")
async def perform_ocr(
    file: UploadFile = File(...),
    preprocess: Optional[str] = Form("auto"),
    psm: Optional[int] = Form(3),
    confidence: Optional[bool] = Form(False),
    mode: Optional[str] = Form("tmz_only"),
    columns: Optional[int] = Form(1),
):
    """
    Reconnaissance de texte Tamazight Latin sur une image.

    - **file**: Image (PNG, JPG, TIFF, BMP, WebP)
    - **preprocess**: Mode de prétraitement (`auto`, `raw`, `binarize`)
    - **psm**: Page Segmentation Mode de Tesseract (3=auto, 6=bloc, 7=ligne, 13=ligne brute)
    - **confidence**: Si true, retourne aussi les scores de confiance par mot
    - **mode**: `hybrid` (fra+tmz_latn, recommandé), `tmz_only` (tmz_latn seul), `kab_only` (kab Bouaziz seul), `compare` (tmz_latn vs kab côte à côte)
    - **columns**: Nombre de colonnes (1=normal, 2=dictionnaire/lexique)
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Le fichier doit être une image (PNG, JPG, TIFF, BMP, WebP).")

    try:
        content = await file.read()
        image = Image.open(io.BytesIO(content))

        # Découpage en colonnes si demandé
        num_cols = columns or 1
        if num_cols > 1:
            col_images = split_image_columns(image, num_cols)
            all_texts = []
            all_confs = []
            for col_img in col_images:
                col_processed = preprocess_image(col_img, mode=preprocess or "auto")
                col_psm = auto_detect_psm(col_img, user_psm=psm or 3)
                col_config = f"--psm {col_psm}"
                ocr_mode = mode or "hybrid"
                if ocr_mode == "hybrid":
                    col_result = hybrid_ocr(col_processed, config=col_config)
                elif ocr_mode == "kab_only":
                    col_data = pytesseract.image_to_data(col_processed, lang="kab", config=col_config, output_type=pytesseract.Output.DICT)
                    col_words = [col_data["text"][i] for i in range(len(col_data["text"])) if col_data["text"][i].strip()]
                    col_confs_list = [col_data["conf"][i] for i in range(len(col_data["text"])) if col_data["text"][i].strip() and col_data["conf"][i] > 0]
                    col_result = {"text": " ".join(col_words), "avg_confidence": sum(col_confs_list) / len(col_confs_list) if col_confs_list else 0}
                else:  # tmz_only ou fallback
                    col_data = pytesseract.image_to_data(col_processed, lang="tmz_latn", config=col_config, output_type=pytesseract.Output.DICT)
                    col_words = [col_data["text"][i] for i in range(len(col_data["text"])) if col_data["text"][i].strip()]
                    col_confs_list = [col_data["conf"][i] for i in range(len(col_data["text"])) if col_data["text"][i].strip() and col_data["conf"][i] > 0]
                    col_result = {"text": " ".join(col_words), "avg_confidence": sum(col_confs_list) / len(col_confs_list) if col_confs_list else 0}
                all_texts.append(col_result["text"])
                all_confs.append(col_result.get("avg_confidence", 0))

            combined_text = "\n\n--- Colonne 2 ---\n\n".join(all_texts)
            avg_conf = sum(all_confs) / len(all_confs) if all_confs else 0
            return JSONResponse(content={
                "mode": mode or "hybrid",
                "columns": num_cols,
                "text": combined_text,
                "filename": file.filename,
                "image_size": {"width": image.size[0], "height": image.size[1]},
                "preprocess": preprocess or "auto",
                "avg_confidence": round(avg_conf, 1),
            })

        # Mode normal (1 colonne)
        # Prétraitement
        processed = preprocess_image(image, mode=preprocess or "auto")

        # Détection automatique du PSM selon la forme de l'image
        effective_psm = auto_detect_psm(image, user_psm=psm or 3)
        config = f"--psm {effective_psm}"
        ocr_mode = mode or "hybrid"

        if ocr_mode == "hybrid":
            # Mode hybride : fra (lettres latines) + tmz_latn (caractères spéciaux)
            hybrid_result = hybrid_ocr(processed, config=config)
            result = {
                "mode": "hybrid",
                "text": hybrid_result["text"],
                "filename": file.filename,
                "image_size": {"width": image.size[0], "height": image.size[1]},
                "preprocess": preprocess or "auto",
                "psm": effective_psm,
                "psm_auto_adjusted": effective_psm != (psm or 3),
                "avg_confidence": hybrid_result["avg_confidence"],
                "sources": hybrid_result["sources"],
                "timestamp": datetime.now().isoformat(),
            }
            if confidence:
                result["words"] = hybrid_result["words"]

        elif ocr_mode == "compare":
            # Mode comparaison : exécuter tmz_latn ET kab côte à côte
            text_tmz = pytesseract.image_to_string(processed, lang="tmz_latn", config=config)
            data_tmz = pytesseract.image_to_data(
                processed, lang="tmz_latn", config=config, output_type=pytesseract.Output.DICT
            )
            tmz_words = [w for w in data_tmz["text"] if w.strip()]
            tmz_confs = [data_tmz["conf"][i] for i, w in enumerate(data_tmz["text"]) if w.strip()]

            text_kab = pytesseract.image_to_string(processed, lang="kab", config=config)
            data_kab = pytesseract.image_to_data(
                processed, lang="kab", config=config, output_type=pytesseract.Output.DICT
            )
            kab_words = [w for w in data_kab["text"] if w.strip()]
            kab_confs = [data_kab["conf"][i] for i, w in enumerate(data_kab["text"]) if w.strip()]

            result = {
                "mode": "compare",
                "tmz_latn": {
                    "text": text_tmz.strip(),
                    "avg_confidence": round(sum(tmz_confs) / len(tmz_confs), 1) if tmz_confs else 0,
                    "word_count": len(tmz_words),
                },
                "kab": {
                    "text": text_kab.strip(),
                    "avg_confidence": round(sum(kab_confs) / len(kab_confs), 1) if kab_confs else 0,
                    "word_count": len(kab_words),
                },
                "filename": file.filename,
                "image_size": {"width": image.size[0], "height": image.size[1]},
                "preprocess": preprocess or "auto",
                "psm": effective_psm,
                "timestamp": datetime.now().isoformat(),
            }

        elif ocr_mode == "kab_only":
            # Mode kab seul (modèle Bouaziz Ait Driss)
            text = pytesseract.image_to_string(processed, lang="kab", config=config)
            result = {
                "mode": "kab_only",
                "text": text.strip(),
                "filename": file.filename,
                "image_size": {"width": image.size[0], "height": image.size[1]},
                "preprocess": preprocess or "auto",
                "psm": effective_psm,
                "timestamp": datetime.now().isoformat(),
            }
            if confidence:
                data = pytesseract.image_to_data(processed, lang="kab", config=config, output_type=pytesseract.Output.DICT)
                words = []
                for i, word in enumerate(data["text"]):
                    if word.strip():
                        words.append({
                            "text": word,
                            "confidence": data["conf"][i],
                            "x": data["left"][i],
                            "y": data["top"][i],
                            "w": data["width"][i],
                            "h": data["height"][i],
                        })
                result["words"] = words
                if words:
                    result["avg_confidence"] = round(sum(w["confidence"] for w in words) / len(words), 1)

        else:
            # Mode tmz_latn seul
            text = pytesseract.image_to_string(processed, lang="tmz_latn", config=config)
            result = {
                "mode": "tmz_only",
                "text": text.strip(),
                "filename": file.filename,
                "image_size": {"width": image.size[0], "height": image.size[1]},
                "preprocess": preprocess or "auto",
                "psm": psm or 3,
                "timestamp": datetime.now().isoformat(),
            }
            if confidence:
                data = pytesseract.image_to_data(processed, lang="tmz_latn", config=config, output_type=pytesseract.Output.DICT)
                words = []
                for i, word in enumerate(data["text"]):
                    if word.strip():
                        words.append({
                            "text": word,
                            "confidence": data["conf"][i],
                            "x": data["left"][i],
                            "y": data["top"][i],
                            "w": data["width"][i],
                            "h": data["height"][i],
                        })
                result["words"] = words
                if words:
                    result["avg_confidence"] = round(sum(w["confidence"] for w in words) / len(words), 1)

        return result

    except pytesseract.TesseractError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur Tesseract: {str(e)}. Vérifiez que tmz_latn.traineddata est dans {MODELS_DIR}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


def _single_lang_ocr(image, lang: str, config: str) -> dict:
    """OCR avec un seul modèle, retourne texte + confiance globale + confiance spéciale."""
    data = pytesseract.image_to_data(image, lang=lang, config=config, output_type=pytesseract.Output.DICT)
    words = [normalize_tmz(data["text"][i]) for i in range(len(data["text"])) if data["text"][i].strip()]
    confs = [data["conf"][i] for i in range(len(data["text"])) if data["text"][i].strip() and data["conf"][i] > 0]
    special_confs = [data["conf"][i] for i in range(len(data["text"])) if data["text"][i].strip() and data["conf"][i] > 0 and has_tamazight_chars(normalize_tmz(data["text"][i]))]
    special_words = [normalize_tmz(data["text"][i]) for i in range(len(data["text"])) if data["text"][i].strip() and has_tamazight_chars(normalize_tmz(data["text"][i]))]
    text = " ".join(words)
    special = count_special_chars(text)
    return {
        "text": text,
        "avg_confidence": round(sum(confs) / len(confs), 1) if confs else 0,
        "special_confidence": round(sum(special_confs) / len(special_confs), 1) if special_confs else 0,
        "special_count": len(special_words),
        "special_detail": special,
    }


def ocr_single_image(image: Image.Image, preprocess_mode: str, psm: int, mode: str, num_cols: int) -> dict:
    """Traite une seule image avec OCR (utilisé par les endpoints image et PDF)."""
    if num_cols > 1:
        col_images = split_image_columns(image, num_cols)
        all_texts = []
        all_confs = []
        all_special_confs = []
        all_special_counts = []
        for col_img in col_images:
            col_processed = preprocess_image(col_img, mode=preprocess_mode)
            col_psm = auto_detect_psm(col_img, user_psm=psm)
            col_config = f"--psm {col_psm}"
            if mode == "hybrid":
                col_result = hybrid_ocr(col_processed, config=col_config)
            elif mode == "kab_only":
                col_result = _single_lang_ocr(col_processed, "kab", col_config)
            else:
                col_result = _single_lang_ocr(col_processed, "tmz_latn", col_config)
            all_texts.append(col_result["text"])
            all_confs.append(col_result.get("avg_confidence", 0))
            all_special_confs.append(col_result.get("special_confidence", 0))
            all_special_counts.append(col_result.get("special_count", 0))
        text = "\n\n--- Colonne 2 ---\n\n".join(all_texts)
        avg_conf = sum(all_confs) / len(all_confs) if all_confs else 0
        # Moyenne pondérée par le nombre de mots spéciaux
        total_special = sum(all_special_counts)
        if total_special > 0:
            special_conf = sum(sc * cnt for sc, cnt in zip(all_special_confs, all_special_counts)) / total_special
        else:
            special_conf = 0
        special = count_special_chars(text)
        return {"text": text, "avg_confidence": round(avg_conf, 1), "special_confidence": round(special_conf, 1), "special_count": total_special, "special_detail": special}
    else:
        processed = preprocess_image(image, mode=preprocess_mode)
        effective_psm = auto_detect_psm(image, user_psm=psm)
        config = f"--psm {effective_psm}"
        if mode == "hybrid":
            result = hybrid_ocr(processed, config=config)
            return {"text": result["text"], "avg_confidence": result["avg_confidence"], "special_confidence": result.get("special_confidence", 0), "special_count": result.get("special_count", 0), "special_detail": result.get("special_detail", {})}
        else:
            lang = "kab" if mode == "kab_only" else "tmz_latn"
            return _single_lang_ocr(processed, lang, config)


@app.post("/api/ocr-pdf")
async def perform_pdf_ocr(
    file: UploadFile = File(...),
    preprocess: Optional[str] = Form("auto"),
    psm: Optional[int] = Form(3),
    mode: Optional[str] = Form("tmz_only"),
    columns: Optional[int] = Form(1),
    pages: Optional[str] = Form("all"),
    dpi: Optional[int] = Form(150),
):
    """
    OCR sur un fichier PDF — convertit chaque page en image puis lance l'OCR.

    - **file**: Fichier PDF
    - **preprocess**: Mode de prétraitement (`auto`, `raw`, `binarize`)
    - **psm**: Page Segmentation Mode (3=auto)
    - **mode**: `hybrid`, `tmz_only`, `kab_only`
    - **columns**: Nombre de colonnes (1=normal, 2=dictionnaire)
    - **pages**: Pages à traiter (`all`, `1-5`, `3,7,12`, `5`)
    - **dpi**: Résolution de rendu (150-600, défaut 300)
    """
    if not HAS_PDF2IMAGE:
        raise HTTPException(status_code=500, detail="pdf2image non installé. Installez avec: pip install pdf2image")

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF.")

    try:
        content = await file.read()
        render_dpi = min(max(dpi or 300, 150), 600)

        # Convertir le PDF en images
        images = convert_from_bytes(content, dpi=render_dpi)
        total_pages = len(images)

        # Parser la sélection de pages
        page_indices = []
        pages_str = pages or "all"
        if pages_str == "all":
            page_indices = list(range(total_pages))
        else:
            for part in pages_str.split(","):
                part = part.strip()
                if "-" in part:
                    start, end = part.split("-", 1)
                    start = max(1, int(start))
                    end = min(total_pages, int(end))
                    page_indices.extend(range(start - 1, end))
                else:
                    idx = int(part) - 1
                    if 0 <= idx < total_pages:
                        page_indices.append(idx)

        if not page_indices:
            raise HTTPException(status_code=400, detail=f"Aucune page valide. Le PDF contient {total_pages} pages.")

        # Traiter chaque page
        ocr_mode = mode or "hybrid"
        num_cols = columns or 1
        preprocess_mode = preprocess or "auto"
        effective_psm = psm or 3

        page_results = []
        all_texts = []

        for page_idx in page_indices:
            page_image = images[page_idx]
            result = ocr_single_image(page_image, preprocess_mode, effective_psm, ocr_mode, num_cols)
            page_results.append({
                "page": page_idx + 1,
                "text": result["text"],
                "avg_confidence": result["avg_confidence"],
                "special_confidence": result.get("special_confidence", 0),
                "special_count": result.get("special_count", 0),
                "image_size": {"width": page_image.size[0], "height": page_image.size[1]},
            })
            all_texts.append(f"--- Page {page_idx + 1} ---\n{result['text']}")

        # Statistiques globales
        avg_conf_global = sum(p["avg_confidence"] for p in page_results) / len(page_results) if page_results else 0
        total_special = sum(p["special_count"] for p in page_results)
        if total_special > 0:
            special_conf_global = sum(p["special_confidence"] * p["special_count"] for p in page_results) / total_special
        else:
            special_conf_global = 0

        combined = "\n\n".join(all_texts)
        special_global = count_special_chars(combined)

        # Extraire le texte intégré du PDF (si disponible) pour comparaison
        pdf_comparison = None
        if HAS_FITZ:
            try:
                doc = fitz.open(stream=content, filetype="pdf")
                pdf_texts = []
                for page_idx in page_indices:
                    page = doc[page_idx]
                    pdf_texts.append(normalize_tmz(page.get_text()))
                pdf_text_combined = "\n".join(pdf_texts)
                doc.close()

                if pdf_text_combined.strip():
                    pdf_special = count_special_chars(pdf_text_combined)
                    ocr_detail = special_global["detail"]
                    pdf_detail = pdf_special["detail"]

                    # Comparer caractère par caractère
                    all_chars = set(list(ocr_detail.keys()) + list(pdf_detail.keys()))
                    comparison = {}
                    total_correct = 0
                    total_expected = 0
                    for c in sorted(all_chars):
                        expected = pdf_detail.get(c, 0)
                        found = ocr_detail.get(c, 0)
                        comparison[c] = {"expected": expected, "found": found, "diff": found - expected}
                        total_correct += min(found, expected)
                        total_expected += expected

                    accuracy = round(total_correct / total_expected * 100, 1) if total_expected > 0 else 0

                    pdf_comparison = {
                        "pdf_special": pdf_special,
                        "accuracy": accuracy,
                        "comparison": comparison,
                        "has_embedded_text": True,
                    }
                else:
                    pdf_comparison = {"has_embedded_text": False}
            except Exception:
                pdf_comparison = {"has_embedded_text": False}

        response = {
            "mode": ocr_mode,
            "columns": num_cols,
            "dpi": render_dpi,
            "filename": file.filename,
            "total_pages": total_pages,
            "pages_processed": len(page_results),
            "avg_confidence": round(avg_conf_global, 1),
            "special_confidence": round(special_conf_global, 1),
            "special_count": total_special,
            "special_detail": special_global,
            "combined_text": combined,
            "pages": page_results,
        }
        if pdf_comparison:
            response["pdf_comparison"] = pdf_comparison
        return JSONResponse(content=response)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur OCR PDF: {str(e)}")


@app.post("/api/ocr/batch")
async def perform_batch_ocr(
    files: list[UploadFile] = File(...),
    preprocess: Optional[str] = Form("auto"),
):
    """OCR sur plusieurs images en une seule requête."""
    results = []
    for file in files:
        if not file.content_type or not file.content_type.startswith("image/"):
            results.append({"filename": file.filename, "error": "Pas une image"})
            continue
        try:
            content = await file.read()
            image = Image.open(io.BytesIO(content))
            processed = preprocess_image(image, mode=preprocess or "auto")
            text = pytesseract.image_to_string(processed, lang="tmz_latn")
            results.append({
                "filename": file.filename,
                "text": text.strip(),
                "image_size": {"width": image.size[0], "height": image.size[1]},
            })
        except Exception as e:
            results.append({"filename": file.filename, "error": str(e)})

    return {"results": results, "total": len(results), "timestamp": datetime.now().isoformat()}


# ── Comparaison de textes ──────────────────────────────────────

# Les 22 caractères spécifiques au Tamazight Latin
TMZ_CHARS_LIST = list("čḍǧḥɣṛṣṭẓɛţČḌǦḤƔṚṢṬẒƐŢ")

@app.post("/api/compare")
async def compare_texts(
    original: str = Form(...),
    ocr_result: str = Form(...),
):
    """
    Compare le texte original avec le résultat OCR.
    Se concentre sur les 20 caractères spécifiques au Tamazight Latin :
    Minuscules : č ḍ ǧ ḥ ɣ ṛ ṣ ṭ ẓ ɛ
    Majuscules : Č Ḍ Ǧ Ḥ Ɣ Ṛ Ṣ Ṭ Ẓ Ɛ

    Pour chaque lettre, retourne le % de reconnaissance et le % d'échec.
    """
    orig = original.replace('\r\n', '\n').strip()
    ocr = ocr_result.replace('\r\n', '\n').strip()

    # Aligner les deux textes caractère par caractère via SequenceMatcher
    matcher = difflib.SequenceMatcher(None, orig, ocr)
    opcodes = matcher.get_opcodes()

    # Construire un mapping : pour chaque position de l'original, quel caractère OCR ?
    char_mapping = {}
    diff_segments = []

    for tag, i1, i2, j1, j2 in opcodes:
        if tag == 'equal':
            for k, idx in enumerate(range(i1, i2)):
                char_mapping[idx] = (orig[idx], orig[idx])
            diff_segments.append({
                "type": "equal",
                "original": orig[i1:i2],
                "ocr": orig[i1:i2],
            })

        elif tag == 'replace':
            orig_chunk = orig[i1:i2]
            ocr_chunk = ocr[j1:j2]
            max_len = max(len(orig_chunk), len(ocr_chunk))
            for k in range(max_len):
                orig_c = orig_chunk[k] if k < len(orig_chunk) else None
                ocr_c = ocr_chunk[k] if k < len(ocr_chunk) else None
                if orig_c is not None:
                    char_mapping[i1 + k] = (orig_c, ocr_c if ocr_c else "∅")
            diff_segments.append({
                "type": "replace",
                "original": orig_chunk,
                "ocr": ocr_chunk,
            })

        elif tag == 'delete':
            for idx in range(i1, i2):
                char_mapping[idx] = (orig[idx], "∅")
            diff_segments.append({
                "type": "delete",
                "original": orig[i1:i2],
                "ocr": "",
            })

        elif tag == 'insert':
            diff_segments.append({
                "type": "insert",
                "original": "",
                "ocr": ocr[j1:j2],
            })

    # Analyser uniquement les 20 caractères Tamazight
    tmz_chars_set = set(TMZ_CHARS_LIST)
    char_stats = {}
    for tmz_char in TMZ_CHARS_LIST:
        char_stats[tmz_char] = {
            "total": 0,
            "recognized": 0,
            "failed": 0,
            "confusions": {},
        }

    for idx, (orig_c, ocr_c) in char_mapping.items():
        if orig_c in tmz_chars_set:
            stats = char_stats[orig_c]
            stats["total"] += 1
            if ocr_c == orig_c:
                stats["recognized"] += 1
            else:
                stats["failed"] += 1
                conf_char = ocr_c if ocr_c else "∅"
                stats["confusions"][conf_char] = stats["confusions"].get(conf_char, 0) + 1

    # Construire le tableau de résultats
    char_table = []
    for tmz_char in TMZ_CHARS_LIST:
        s = char_stats[tmz_char]
        if s["total"] == 0:
            pct_ok = None
            pct_fail = None
        else:
            pct_ok = round(100 * s["recognized"] / s["total"], 1)
            pct_fail = round(100 * s["failed"] / s["total"], 1)

        top_confusions = sorted(s["confusions"].items(), key=lambda x: -x[1])

        char_table.append({
            "char": tmz_char,
            "total": s["total"],
            "recognized": s["recognized"],
            "failed": s["failed"],
            "pct_recognized": pct_ok,
            "pct_failed": pct_fail,
            "confusions": [{"char": c, "count": n} for c, n in top_confusions[:3]],
        })

    # Statistiques globales
    total_tmz = sum(s["total"] for s in char_stats.values())
    total_ok = sum(s["recognized"] for s in char_stats.values())
    total_fail = sum(s["failed"] for s in char_stats.values())

    return {
        "diff_segments": diff_segments,
        "char_table": char_table,
        "global_stats": {
            "total_tmz_chars": total_tmz,
            "recognized": total_ok,
            "failed": total_fail,
            "pct_recognized": round(100 * total_ok / total_tmz, 1) if total_tmz > 0 else 0,
            "pct_failed": round(100 * total_fail / total_tmz, 1) if total_tmz > 0 else 0,
            "similarity": round(matcher.ratio() * 100, 1),
        },
        "timestamp": datetime.now().isoformat(),
    }


# ── Servir les fichiers statiques ──────────────────────────────
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
