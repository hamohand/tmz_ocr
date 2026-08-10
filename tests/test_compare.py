#!/usr/bin/env python3
"""
Test comparatif : tmz_latn vs kab sur de vrais documents scannés.
Exécute les deux modèles Tesseract sur chaque image et compare les résultats.

Usage: python3 test_compare.py
"""
import os
import sys
import pytesseract
from PIL import Image

# Configuration
SAMPLES_DIR = "/mnt/c/Users/hamoh/Documents/travail/tmz/tmz_ocr/tests/samples"
MODELS_DIR = "/mnt/c/Users/hamoh/Documents/travail/tmz/tmz_ocr/models"
os.environ["TESSDATA_PREFIX"] = MODELS_DIR

# Caractères spéciaux Tamazight
TMZ_SPECIAL = set("čḍǧḥɣṛṣṭẓɛţČḌǦḤƔṚṢṬẒƐŢ")

def count_special_chars(text):
    """Compte les caractères spéciaux Tamazight dans un texte."""
    return sum(1 for c in text if c in TMZ_SPECIAL)

def run_ocr(image_path, lang, psm=3):
    """Lance Tesseract OCR sur une image avec un modèle donné."""
    try:
        img = Image.open(image_path)
        config = f"--psm {psm}"
        text = pytesseract.image_to_string(img, lang=lang, config=config)
        data = pytesseract.image_to_data(img, lang=lang, config=config, output_type=pytesseract.Output.DICT)
        
        words = [w for w in data["text"] if w.strip()]
        confs = [data["conf"][i] for i, w in enumerate(data["text"]) if w.strip() and data["conf"][i] >= 0]
        avg_conf = sum(confs) / len(confs) if confs else 0
        
        return {
            "text": text.strip(),
            "word_count": len(words),
            "avg_confidence": round(avg_conf, 1),
            "special_chars": count_special_chars(text),
            "char_count": len(text.strip()),
        }
    except Exception as e:
        return {"text": "", "error": str(e), "word_count": 0, "avg_confidence": 0, "special_chars": 0, "char_count": 0}


def main():
    print("=" * 70)
    print("⚔️  Test comparatif : tmz_latn vs kab sur vrais scans")
    print("=" * 70)
    
    # Vérifier les modèles
    for model in ["tmz_latn", "kab"]:
        path = os.path.join(MODELS_DIR, f"{model}.traineddata")
        if os.path.exists(path):
            size = os.path.getsize(path) / 1024 / 1024
            print(f"  ✓ {model}.traineddata ({size:.1f} MB)")
        else:
            print(f"  ❌ {model}.traineddata NON TROUVÉ")
            return
    
    # Lister les images
    images = sorted([
        f for f in os.listdir(SAMPLES_DIR) 
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp'))
    ])
    
    if not images:
        print(f"\n❌ Aucune image trouvée dans {SAMPLES_DIR}")
        return
    
    print(f"\n📁 {len(images)} images de test trouvées")
    print("-" * 70)
    
    # Résultats globaux
    results = []
    
    for img_file in images:
        img_path = os.path.join(SAMPLES_DIR, img_file)
        img_size = os.path.getsize(img_path) / 1024
        
        print(f"\n📄 {img_file} ({img_size:.0f} KB)")
        
        # OCR avec les deux modèles
        print(f"   🔄 tmz_latn...", end="", flush=True)
        tmz = run_ocr(img_path, "tmz_latn")
        print(f" ✓ ({tmz['word_count']} mots, {tmz['avg_confidence']}% conf.)")
        
        print(f"   🔄 kab...", end="", flush=True)
        kab = run_ocr(img_path, "kab")
        print(f" ✓ ({kab['word_count']} mots, {kab['avg_confidence']}% conf.)")
        
        # Comparaison
        print(f"   ┌──────────────────┬──────────────┬──────────────┐")
        print(f"   │ Métrique         │   tmz_latn   │     kab      │")
        print(f"   ├──────────────────┼──────────────┼──────────────┤")
        print(f"   │ Mots détectés    │ {tmz['word_count']:>12} │ {kab['word_count']:>12} │")
        print(f"   │ Confiance moy.   │ {tmz['avg_confidence']:>11}% │ {kab['avg_confidence']:>11}% │")
        print(f"   │ Car. spéciaux    │ {tmz['special_chars']:>12} │ {kab['special_chars']:>12} │")
        print(f"   │ Caractères total │ {tmz['char_count']:>12} │ {kab['char_count']:>12} │")
        print(f"   └──────────────────┴──────────────┴──────────────┘")
        
        # Aperçu des 3 premières lignes
        tmz_lines = tmz['text'].split('\n')[:3]
        kab_lines = kab['text'].split('\n')[:3]
        print(f"   📝 tmz_latn (3 premières lignes):")
        for line in tmz_lines:
            if line.strip():
                print(f"      {line.strip()[:80]}")
        print(f"   📝 kab (3 premières lignes):")
        for line in kab_lines:
            if line.strip():
                print(f"      {line.strip()[:80]}")
        
        results.append({
            "file": img_file,
            "tmz": tmz,
            "kab": kab,
        })
    
    # Résumé global
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ GLOBAL")
    print("=" * 70)
    
    total_tmz_conf = sum(r["tmz"]["avg_confidence"] for r in results) / len(results)
    total_kab_conf = sum(r["kab"]["avg_confidence"] for r in results) / len(results)
    total_tmz_special = sum(r["tmz"]["special_chars"] for r in results)
    total_kab_special = sum(r["kab"]["special_chars"] for r in results)
    total_tmz_words = sum(r["tmz"]["word_count"] for r in results)
    total_kab_words = sum(r["kab"]["word_count"] for r in results)
    
    print(f"\n   ┌──────────────────────┬──────────────┬──────────────┐")
    print(f"   │ Métrique globale     │   tmz_latn   │     kab      │")
    print(f"   ├──────────────────────┼──────────────┼──────────────┤")
    print(f"   │ Confiance moyenne    │ {total_tmz_conf:>11.1f}% │ {total_kab_conf:>11.1f}% │")
    print(f"   │ Total mots détectés  │ {total_tmz_words:>12} │ {total_kab_words:>12} │")
    print(f"   │ Total car. spéciaux  │ {total_tmz_special:>12} │ {total_kab_special:>12} │")
    print(f"   └──────────────────────┴──────────────┴──────────────┘")
    
    winner_conf = "tmz_latn" if total_tmz_conf > total_kab_conf else "kab"
    winner_special = "tmz_latn" if total_tmz_special > total_kab_special else "kab"
    
    print(f"\n   🏆 Meilleure confiance : {winner_conf}")
    print(f"   🏆 Plus de car. spéciaux détectés : {winner_special}")
    print(f"\n✅ Test terminé !")


if __name__ == "__main__":
    main()
