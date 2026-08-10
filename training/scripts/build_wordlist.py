#!/usr/bin/env python3
"""
Générateur de wordlist enrichie pour Tesseract — tmz_latn
Combine les mots du corpus local + télécharge le corpus complet Sifal/Kabyle-French.

Usage: python3 build_wordlist.py
Sortie: ../data/tmz_latn.wordlist (nettoyé, trié, dédupliqué)
"""
import os
import re
import sys
import json
import urllib.request
import unicodedata

# ==============================================================================
# CONFIGURATION
# ==============================================================================
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_WORDLIST = os.path.join(SCRIPTS_DIR, "..", "data", "tmz_latn.wordlist")

# Fichiers corpus locaux
LOCAL_CORPUS_FILES = [
    os.path.join(SCRIPTS_DIR, "lignes_tamazight.txt"),
    os.path.join(SCRIPTS_DIR, "lignes_tamazight_enrichi.txt"),
    os.path.join(SCRIPTS_DIR, "lignes_tamazight_v3.txt"),
    os.path.join(SCRIPTS_DIR, "lignes_tamazight_renforce.txt"),
]

# Dataset HuggingFace : Sifal/Kabyle-French (115 269 paires)
HF_DATASET_URL = "https://datasets-server.huggingface.co/rows?dataset=Sifal%2FKabyle-French&config=default&split=train&offset={offset}&length={length}"
HF_BATCH_SIZE = 100
HF_MAX_ROWS = 115269  # Nombre total de lignes dans le dataset

# Caractères latins Tamazight spéciaux (pour filtrage)
TMZ_SPECIAL = set("čḍǧḥɣṛṣṭẓɛţČḌǦḤƔṚṢṬẒƐŢ")

# Caractères autorisés dans un mot (lettres latines, tamazight, apostrophes, tirets)
WORD_PATTERN = re.compile(r"^[a-zA-ZàâäéèêëïîôùûüÿçœæÀÂÄÉÈÊËÏÎÔÙÛÜŸÇŒÆčḍǧḥɣṛṣṭẓɛţČḌǦḤƔṚṢṬẒƐŢεԐ][a-zA-ZàâäéèêëïîôùûüÿçœæÀÂÄÉÈÊËÏÎÔÙÛÜŸÇŒÆčḍǧḥɣṛṣṭẓɛţČḌǦḤƔṚṢṬẒƐŢεԐ'\-]*$")


def extract_words(text):
    """Extrait les mots d'un texte, nettoie la ponctuation."""
    words = set()
    # Découper par espaces et ponctuation
    tokens = re.split(r'[\s,;:!?.()\[\]{}"«»…\t\n]+', text)
    for token in tokens:
        # Nettoyer les guillemets et ponctuation en début/fin
        token = token.strip("'\"''""-–—_/\\|<>*+#@&=^~`")
        if not token or len(token) < 2:
            continue
        # Vérifier que c'est un vrai mot (pas un nombre, pas un symbole)
        if WORD_PATTERN.match(token):
            words.add(token)
    return words


def load_local_corpus():
    """Charge les mots depuis les fichiers corpus locaux."""
    all_words = set()
    for filepath in LOCAL_CORPUS_FILES:
        if not os.path.exists(filepath):
            print(f"  ⚠ Fichier non trouvé : {os.path.basename(filepath)}")
            continue
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        words = extract_words(text)
        print(f"  ✓ {os.path.basename(filepath)} : {len(words)} mots uniques")
        all_words.update(words)
    return all_words


def download_hf_corpus(max_rows=None):
    """Télécharge les phrases kabyles depuis HuggingFace et en extrait les mots."""
    if max_rows is None:
        max_rows = HF_MAX_ROWS

    all_words = set()
    offset = 0
    total_sentences = 0

    print(f"\n📡 Téléchargement du corpus Sifal/Kabyle-French ({max_rows} lignes max)...")

    while offset < max_rows:
        batch_size = min(HF_BATCH_SIZE, max_rows - offset)
        url = HF_DATASET_URL.format(offset=offset, length=batch_size)

        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "tmz-ocr-wordlist/1.0")
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            rows = data.get("rows", [])
            if not rows:
                break

            for row in rows:
                # Le champ kabyle peut être 'kab' ou 'Kabyle' selon la config
                row_data = row.get("row", {})
                kab_text = row_data.get("kab", "") or row_data.get("Kabyle", "") or ""
                if kab_text:
                    words = extract_words(kab_text)
                    all_words.update(words)
                    total_sentences += 1

            offset += len(rows)
            if offset % 5000 == 0 or offset >= max_rows:
                print(f"  📥 {offset}/{max_rows} lignes — {len(all_words)} mots uniques")

        except urllib.error.URLError as e:
            print(f"  ❌ Erreur réseau à offset {offset}: {e}")
            print(f"  ⏭ Passage au batch suivant...")
            offset += batch_size
        except json.JSONDecodeError as e:
            print(f"  ❌ Erreur JSON à offset {offset}: {e}")
            offset += batch_size
        except Exception as e:
            print(f"  ❌ Erreur inattendue à offset {offset}: {e}")
            break

    print(f"  ✓ {total_sentences} phrases kabyles → {len(all_words)} mots uniques")
    return all_words


def analyze_wordlist(words):
    """Analyse la wordlist : statistiques sur les caractères spéciaux."""
    total = len(words)
    with_special = sum(1 for w in words if any(c in TMZ_SPECIAL for c in w))

    # Fréquence de chaque caractère spécial
    char_freq = {}
    for w in words:
        for c in w:
            if c in TMZ_SPECIAL:
                char_freq[c] = char_freq.get(c, 0) + 1

    print(f"\n📊 Statistiques de la wordlist :")
    print(f"   Total mots : {total}")
    print(f"   Mots avec car. spéciaux : {with_special} ({100*with_special/total:.1f}%)")
    print(f"   Mots sans car. spéciaux : {total - with_special}")
    print(f"\n   Fréquence des caractères spéciaux :")
    for char, count in sorted(char_freq.items(), key=lambda x: -x[1]):
        print(f"     {char} : {count} occurrences")


def main():
    print("=" * 60)
    print("🔤 Générateur de wordlist enrichie — tmz_latn")
    print("=" * 60)

    # 1. Corpus local
    print("\n📂 Chargement du corpus local...")
    local_words = load_local_corpus()
    print(f"   → {len(local_words)} mots uniques locaux")

    # 2. Corpus HuggingFace (toutes les 115K lignes)
    hf_words = set()
    try:
        hf_words = download_hf_corpus(max_rows=HF_MAX_ROWS)
    except Exception as e:
        print(f"   ⚠ Impossible de télécharger le corpus HF : {e}")
        print(f"   → On continue avec le corpus local uniquement")

    # 3. Fusion et déduplication
    all_words = local_words | hf_words
    new_from_hf = hf_words - local_words
    print(f"\n🔀 Fusion :")
    print(f"   Local : {len(local_words)} mots")
    print(f"   HuggingFace : {len(hf_words)} mots ({len(new_from_hf)} nouveaux)")
    print(f"   Total fusionné : {len(all_words)} mots uniques")

    # 4. Tri et écriture
    sorted_words = sorted(all_words, key=lambda w: w.lower())

    os.makedirs(os.path.dirname(OUTPUT_WORDLIST), exist_ok=True)
    with open(OUTPUT_WORDLIST, "w", encoding="utf-8") as f:
        for word in sorted_words:
            f.write(word + "\n")

    print(f"\n💾 Wordlist écrite : {OUTPUT_WORDLIST}")
    print(f"   {len(sorted_words)} mots")

    # 5. Analyse
    analyze_wordlist(sorted_words)

    # 6. Aperçu
    print(f"\n📖 Aperçu (10 premiers / 10 derniers) :")
    for w in sorted_words[:10]:
        print(f"   {w}")
    print("   ...")
    for w in sorted_words[-10:]:
        print(f"   {w}")

    print(f"\n✅ Wordlist prête pour l'intégration Tesseract")
    print(f"   Copier vers : data/tmz_latn/tmz_latn.wordlist")


if __name__ == "__main__":
    main()
