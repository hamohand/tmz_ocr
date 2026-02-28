import os
import random
from PIL import Image, ImageDraw, ImageFont

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Dossiers d'entrée / sortie
FONTS_DIR = "../data/fonts"
OUTPUT_DIR = "../data/tmz_latn-ground-truth"
INPUT_TEXT_FILE = "lignes_tamazight.txt"

# Paramètres de l'image générée
IMAGE_HEIGHT = 50       # Hauteur fixe de l'image (bon pour l'entraînement LSTM)
FONT_SIZE = 32          # Taille de la police
BG_COLOR = "white"      # Fond blanc
TEXT_COLOR = "black"    # Texte noir

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

def generate_line_image(text, font_path, output_image_path):
    """Génère une image TIF contenant le texte avec la police donnée"""
    try:
        font = ImageFont.truetype(font_path, FONT_SIZE)
        
        # Obtenir la taille du texte pour créer une image de la bonne largeur
        # Pillow >= 10.0 : getbbox ou getlength / ancien Pillow : getsize
        dummy_img = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        
        # Ajouter une petite marge (padding) à gauche et à droite
        padding = 20
        img_width = text_width + (padding * 2)
        
        # Créer l'image finale
        img = Image.new("RGB", (int(img_width), IMAGE_HEIGHT), color=BG_COLOR)
        draw = ImageDraw.Draw(img)
        
        # Centrer verticalement le texte
        text_height = bbox[3] - bbox[1]
        y_pos = (IMAGE_HEIGHT - text_height) / 2 - bbox[1]
        
        draw.text((padding, y_pos), text, font=font, fill=TEXT_COLOR)
        
        # Sauvegarder en TIF (format recommandé par Tesseract)
        img.save(output_image_path, format="TIFF")
        return True
    except Exception as e:
        print(f"Erreur avec la police {font_path}: {e}")
        return False

def main():
    print("=== Générateur de Ground Truth (Tamazight OCR) ===")
    
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
            print(f"[{succes}/{len(lines)}] Généré: {base_name}")
            
    print("\nTerminé !")
    print(f"{succes} paires d'images (.tif) et de textes (.gt.txt) ont été créées dans {OUTPUT_DIR}")
    print("Vous êtes prêt à lancer: make training MODEL_NAME=tmz_latn ... dans tesstrain.")

if __name__ == "__main__":
    main()
