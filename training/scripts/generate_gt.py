import os
import random
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Dossiers d'entrée / sortie
FONTS_DIR = "../data/fonts"
OUTPUT_DIR = "../data/tmz_latn-ground-truth"
INPUT_TEXT_FILE = "lignes_tamazight_v4.txt"

# Paramètres de l'image générée
IMAGE_HEIGHT = 50       # Hauteur fixe de l'image (bon pour l'entraînement LSTM)
FONT_SIZE = 32          # Taille de la police de base
BG_COLOR = "white"      # Fond par défaut
TEXT_COLOR = "black"     # Texte par défaut

# ==============================================================================
# DATA AUGMENTATION — Configuration
# ==============================================================================
# Activer/désactiver l'augmentation globale
AUGMENT_ENABLED = True

# Probabilité de chaque transformation (0.0 = jamais, 1.0 = toujours)
AUGMENT_CONFIG = {
    # ── Bruit ──
    "gaussian_noise": {
        "prob": 0.30,           # 30% des images auront du bruit gaussien
        "intensity_range": (5, 20),  # Écart-type du bruit (pixels 0-255)
    },
    "salt_pepper": {
        "prob": 0.15,           # 15% des images auront du bruit poivre & sel
        "density_range": (0.002, 0.01),  # Densité des pixels affectés
    },

    # ── Géométrie ──
    "rotation": {
        "prob": 0.25,           # 25% des images seront légèrement tournées
        "angle_range": (-2.0, 2.0),  # Angle en degrés
    },

    # ── Flou ──
    "blur": {
        "prob": 0.20,           # 20% des images seront légèrement floues
        "radius_range": (0.5, 1.5),  # Rayon du flou gaussien
    },

    # ── Contraste / Luminosité ──
    "contrast": {
        "prob": 0.30,           # 30% des images auront un contraste modifié
        "factor_range": (0.7, 1.3),  # 1.0 = original
    },
    "brightness": {
        "prob": 0.25,           # 25% des images auront une luminosité modifiée
        "factor_range": (0.8, 1.2),  # 1.0 = original
    },

    # ── Fond ──
    "background": {
        "prob": 0.35,           # 35% des images auront un fond non-blanc
        # Types de fonds possibles (pondérés)
        "types": ["gray", "beige", "noisy_white", "gradient"],
    },

    # ── Taille de police variable ──
    "font_size_variation": {
        "prob": 0.40,           # 40% des images auront une taille de police différente
        "size_range": (26, 40),  # Min-max de la taille de police
    },

    # ── Épaisseur de texte (simulée par léger décalage) ──
    "text_color_variation": {
        "prob": 0.20,           # 20% des images auront un texte gris foncé au lieu de noir
        "gray_range": (0, 80),  # Valeur de gris (0=noir, 80=gris foncé)
    },
}

# ==============================================================================

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_fonts(fonts_dir):
    """Retourne la liste des chemins des polices .ttf ou .otf dans le dossier"""
    fonts = []
    if os.path.exists(fonts_dir):
        for f in os.listdir(fonts_dir):
            if f.lower().endswith(('.ttf', '.otf')):
                fonts.append(os.path.join(fonts_dir, f))
    return fonts


# ==============================================================================
# FONCTIONS D'AUGMENTATION
# ==============================================================================

def apply_gaussian_noise(img, config):
    """Ajoute du bruit gaussien à l'image."""
    arr = np.array(img, dtype=np.float32)
    lo, hi = config["intensity_range"]
    sigma = random.uniform(lo, hi)
    noise = np.random.normal(0, sigma, arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def apply_salt_pepper(img, config):
    """Ajoute du bruit poivre & sel."""
    arr = np.array(img)
    lo, hi = config["density_range"]
    density = random.uniform(lo, hi)
    total_pixels = arr.shape[0] * arr.shape[1]
    n_salt = int(total_pixels * density)
    n_pepper = int(total_pixels * density)

    # Sel (pixels blancs)
    for _ in range(n_salt):
        y = random.randint(0, arr.shape[0] - 1)
        x = random.randint(0, arr.shape[1] - 1)
        arr[y, x] = 255 if len(arr.shape) == 2 else [255, 255, 255]

    # Poivre (pixels noirs)
    for _ in range(n_pepper):
        y = random.randint(0, arr.shape[0] - 1)
        x = random.randint(0, arr.shape[1] - 1)
        arr[y, x] = 0 if len(arr.shape) == 2 else [0, 0, 0]

    return Image.fromarray(arr)


def apply_rotation(img, config):
    """Applique une légère rotation."""
    lo, hi = config["angle_range"]
    angle = random.uniform(lo, hi)
    return img.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=(255, 255, 255))


def apply_blur(img, config):
    """Applique un flou gaussien léger."""
    lo, hi = config["radius_range"]
    radius = random.uniform(lo, hi)
    return img.filter(ImageFilter.GaussianBlur(radius=radius))


def apply_contrast(img, config):
    """Modifie le contraste de l'image."""
    lo, hi = config["factor_range"]
    factor = random.uniform(lo, hi)
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(factor)


def apply_brightness(img, config):
    """Modifie la luminosité de l'image."""
    lo, hi = config["factor_range"]
    factor = random.uniform(lo, hi)
    enhancer = ImageEnhance.Brightness(img)
    return enhancer.enhance(factor)


def generate_background(width, height, bg_type):
    """Génère un fond non-blanc pour simuler différents types de papier."""
    if bg_type == "gray":
        # Fond gris uniforme (comme du papier recyclé)
        gray = random.randint(220, 245)
        return Image.new("RGB", (width, height), (gray, gray, gray))

    elif bg_type == "beige":
        # Fond beige/jauni (comme du vieux papier)
        r = random.randint(230, 250)
        g = random.randint(220, 240)
        b = random.randint(200, 220)
        return Image.new("RGB", (width, height), (r, g, b))

    elif bg_type == "noisy_white":
        # Fond blanc avec micro-bruit (comme un scan)
        arr = np.ones((height, width, 3), dtype=np.uint8) * 255
        noise = np.random.normal(0, 3, arr.shape).astype(np.int16)
        arr = np.clip(arr.astype(np.int16) + noise, 200, 255).astype(np.uint8)
        return Image.fromarray(arr)

    elif bg_type == "gradient":
        # Léger dégradé vertical (scan inégal)
        arr = np.zeros((height, width, 3), dtype=np.uint8)
        top = random.randint(240, 255)
        bottom = random.randint(225, 250)
        for y in range(height):
            val = int(top + (bottom - top) * y / height)
            arr[y, :] = [val, val, val]
        return Image.fromarray(arr)

    else:
        return Image.new("RGB", (width, height), "white")


def augment_image(img):
    """Applique les augmentations configurées à une image."""
    if not AUGMENT_ENABLED:
        return img

    cfg = AUGMENT_CONFIG

    # Contraste
    if random.random() < cfg["contrast"]["prob"]:
        img = apply_contrast(img, cfg["contrast"])

    # Luminosité
    if random.random() < cfg["brightness"]["prob"]:
        img = apply_brightness(img, cfg["brightness"])

    # Rotation (avant les bruits pour éviter les artefacts)
    if random.random() < cfg["rotation"]["prob"]:
        img = apply_rotation(img, cfg["rotation"])

    # Flou
    if random.random() < cfg["blur"]["prob"]:
        img = apply_blur(img, cfg["blur"])

    # Bruit gaussien
    if random.random() < cfg["gaussian_noise"]["prob"]:
        img = apply_gaussian_noise(img, cfg["gaussian_noise"])

    # Bruit poivre & sel
    if random.random() < cfg["salt_pepper"]["prob"]:
        img = apply_salt_pepper(img, cfg["salt_pepper"])

    return img


# ==============================================================================
# GÉNÉRATION D'IMAGE
# ==============================================================================

def generate_line_image(text, font_path, output_image_path):
    """Génère une image TIF contenant le texte avec la police donnée + augmentation."""
    try:
        cfg = AUGMENT_CONFIG

        # ── Taille de police variable ──
        font_size = FONT_SIZE
        if AUGMENT_ENABLED and random.random() < cfg["font_size_variation"]["prob"]:
            lo, hi = cfg["font_size_variation"]["size_range"]
            font_size = random.randint(lo, hi)

        font = ImageFont.truetype(font_path, font_size)

        # Obtenir la taille du texte
        dummy_img = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]

        # Ajouter une marge (padding)
        padding = 20
        img_width = text_width + (padding * 2)
        img_height = max(IMAGE_HEIGHT, int(font_size * 1.6))

        # ── Fond ──
        if AUGMENT_ENABLED and random.random() < cfg["background"]["prob"]:
            bg_type = random.choice(cfg["background"]["types"])
            img = generate_background(int(img_width), img_height, bg_type)
        else:
            img = Image.new("RGB", (int(img_width), img_height), color=BG_COLOR)

        draw = ImageDraw.Draw(img)

        # ── Couleur du texte ──
        text_fill = TEXT_COLOR
        if AUGMENT_ENABLED and random.random() < cfg["text_color_variation"]["prob"]:
            lo, hi = cfg["text_color_variation"]["gray_range"]
            g = random.randint(lo, hi)
            text_fill = (g, g, g)

        # Centrer verticalement le texte
        text_height = bbox[3] - bbox[1]
        y_pos = (img_height - text_height) / 2 - bbox[1]

        draw.text((padding, y_pos), text, font=font, fill=text_fill)

        # ── Appliquer les augmentations ──
        img = augment_image(img)

        # Sauvegarder en TIF
        img.save(output_image_path, format="TIFF")
        return True
    except Exception as e:
        print(f"Erreur avec la police {font_path}: {e}")
        return False


def main():
    print("=== Générateur de Ground Truth (Tamazight OCR) ===")
    if AUGMENT_ENABLED:
        print("🎲 Data Augmentation : ACTIVÉE")
        active = [k for k, v in AUGMENT_CONFIG.items() if v.get("prob", 0) > 0]
        print(f"   Transformations actives : {', '.join(active)}")
    else:
        print("⚪ Data Augmentation : DÉSACTIVÉE (images propres)")

    # 1. Vérifications
    ensure_dir(OUTPUT_DIR)
    fonts = get_fonts(FONTS_DIR)

    if not fonts:
        print(f"ERREUR: Aucune police trouvée dans '{FONTS_DIR}'.")
        print("Veuillez y placer au moins un fichier .ttf (ex: Arial, Tahoma, etc.)")
        return

    if not os.path.exists(INPUT_TEXT_FILE):
        print(f"Création d'un fichier d'exemple: {INPUT_TEXT_FILE}")
        with open(INPUT_TEXT_FILE, "w", encoding="utf-8") as f:
            f.write("Azul fellawen\n")
            f.write("Aqvayli d ameslay n tmaziɣt\n")
            f.write("Isekkilen i d-yeṭṭfen amḍiq\n")
            f.write("Awal ɣef yidles amaziɣ\n")
            f.write("Ɛṛeb, Ḥmed, Ṭṭawes\n")

    # 2. Lecture des phrases
    with open(INPUT_TEXT_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    print(f"Trouvé {len(lines)} lignes de texte, et {len(fonts)} polices.")

    # 3. Génération
    succes = 0
    augment_stats = {k: 0 for k in AUGMENT_CONFIG}

    for idx, line_text in enumerate(lines):
        # Choisir une police au hasard pour cette ligne
        font_path = random.choice(fonts)

        # Noms des fichiers (ex: tmz_latn_0001.tif et tmz_latn_0001.gt.txt)
        base_name = f"tmz_latn_{idx:04d}"
        img_file = os.path.join(OUTPUT_DIR, f"{base_name}.tif")
        txt_file = os.path.join(OUTPUT_DIR, f"{base_name}.gt.txt")

        # Générer l'image
        if generate_line_image(line_text, font_path, img_file):
            # Sauvegarder le texte exact correspondant
            with open(txt_file, "w", encoding="utf-8") as f:
                f.write(line_text)
            succes += 1
            if succes % 500 == 0 or succes == len(lines):
                print(f"[{succes}/{len(lines)}] Généré: {base_name}")

    print(f"\nTerminé !")
    print(f"{succes} paires d'images (.tif) et de textes (.gt.txt) créées dans {OUTPUT_DIR}")
    if AUGMENT_ENABLED:
        print(f"🎲 Images augmentées avec : bruit, rotation, flou, contraste, fonds variés")
    print("Vous êtes prêt à lancer: make training MODEL_NAME=tmz_latn ... dans tesstrain.")

if __name__ == "__main__":
    main()



