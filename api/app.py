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
from typing import Optional

# ── Configuration ──────────────────────────────────────────────
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))
os.environ["TESSDATA_PREFIX"] = MODELS_DIR

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# ── App FastAPI ────────────────────────────────────────────────
app = FastAPI(
    title="ⵣ Tamazight OCR API",
    description="API de reconnaissance optique de caractères pour le Tamazight Latin (Kabyle). Modèles : tmz_latn + kab (Bouaziz).",
    version="5.0.0",
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


def split_image_columns(image: Image.Image, num_cols: int = 2, trim_pct: float = 0.02) -> list:
    """Découpe une image en colonnes verticales pour les documents multi-colonnes."""
    w, h = image.size
    trim = int(w * trim_pct)
    mid = w // num_cols
    columns = [
        image.crop((0, 0, mid - trim, h)),
        image.crop((mid - int(w * 0.01), 0, w, h)),
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
TMZ_SPECIAL_CHARS = set("ḍṭṣẓṛḥɛɣčğţεԐƐƔŢ")

def has_tamazight_chars(word: str) -> bool:
    """Vérifie si un mot contient des caractères spécifiques au Tamazight."""
    return any(c in TMZ_SPECIAL_CHARS for c in word)


def hybrid_ocr(image, config: str = "--psm 3") -> dict:
    """
    OCR hybride : combine les résultats de 'fra' et 'tmz_latn'.

    Stratégie :
    - Lancer les 2 modèles sur la même image
    - Pour chaque mot, comparer les résultats :
      1. Si tmz_latn détecte un caractère spécial → garder tmz_latn
      2. Sinon, garder le mot avec la meilleure confiance
    - Reconstruire le texte final
    """
    # OCR avec les deux modèles
    data_tmz = pytesseract.image_to_data(
        image, lang="tmz_latn", config=config, output_type=pytesseract.Output.DICT
    )
    try:
        data_fra = pytesseract.image_to_data(
            image, lang="fra", config=config, output_type=pytesseract.Output.DICT
        )
        has_fra = True
    except pytesseract.TesseractError:
        # Si fra n'est pas disponible, utiliser uniquement tmz_latn
        data_fra = None
        has_fra = False

    # Construire les résultats mot par mot
    words_result = []
    lines = {}  # {(block, par, line): [words]}

    for i, word_tmz in enumerate(data_tmz["text"]):
        if not word_tmz.strip():
            continue

        conf_tmz = data_tmz["conf"][i]
        block = data_tmz["block_num"][i]
        par = data_tmz["par_num"][i]
        line_num = data_tmz["line_num"][i]

        # Chercher le mot correspondant dans fra (même position approximative)
        chosen_word = word_tmz
        chosen_conf = conf_tmz
        chosen_source = "tmz_latn"

        if has_fra and data_fra:
            # Trouver le mot fra le plus proche (même index si possible)
            word_fra = ""
            conf_fra = -1
            if i < len(data_fra["text"]):
                word_fra = data_fra["text"][i]
                conf_fra = data_fra["conf"][i]

            if word_fra.strip():
                if has_tamazight_chars(word_tmz):
                    # tmz_latn a détecté un caractère spécial → le garder
                    chosen_word = word_tmz
                    chosen_conf = conf_tmz
                    chosen_source = "tmz_latn*"  # * = choix forcé
                elif conf_fra > conf_tmz and conf_fra > 0:
                    # fra a une meilleure confiance → le prendre
                    chosen_word = word_fra
                    chosen_conf = conf_fra
                    chosen_source = "fra"

        key = (block, par, line_num)
        if key not in lines:
            lines[key] = []
        lines[key].append(chosen_word)

        words_result.append({
            "text": chosen_word,
            "confidence": chosen_conf,
            "source": chosen_source,
            "tmz": word_tmz,
            "fra": data_fra["text"][i].strip() if (has_fra and data_fra and i < len(data_fra["text"])) else "",
            "x": data_tmz["left"][i],
            "y": data_tmz["top"][i],
            "w": data_tmz["width"][i],
            "h": data_tmz["height"][i],
        })

    # Reconstruire le texte ligne par ligne
    text_lines = []
    for key in sorted(lines.keys()):
        text_lines.append(" ".join(lines[key]))
    final_text = "\n".join(text_lines)

    # Statistiques
    sources = {"tmz_latn": 0, "tmz_latn*": 0, "fra": 0}
    for w in words_result:
        sources[w["source"]] = sources.get(w["source"], 0) + 1

    return {
        "text": final_text,
        "words": words_result,
        "sources": sources,
        "avg_confidence": round(sum(w["confidence"] for w in words_result) / len(words_result), 1) if words_result else 0,
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
    mode: Optional[str] = Form("hybrid"),
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
