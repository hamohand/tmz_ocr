#!/usr/bin/env python3
"""
enrich_labiovelar.py — Ajoute des lignes contenant ʷ et ᵒ au corpus v4
pour créer le corpus v5 avec support des labio-vélarisées.
"""
import os
import random

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Mots kabyles courants avec ʷ (labio-vélarisées)
WORDS_W = [
    "akʷer", "ameqqʷran", "ireggʷel", "yebbʷi", "azeggʷaɣ",
    "ibbʷi", "yebbʷa", "tubbʷin", "tibbʷit", "tibbʷin",
    "neţembʷi", "tebbʷa", "ebbʷ", "yeţţebbʷa", "yeţţebbʷay",
    "bʷiɣ", "temmʷet", "yemmʷet", "nemmʷet", "mmʷet",
    "neggʷra", "yeggʷra", "iggʷra", "aggʷad", "uggʷad",
    "neqqʷel", "yeqqʷel", "iqqʷel", "qqʷel", "aqqʷel",
    "nekkʷni", "kunʷi", "nutʷenti", "aẓekkʷa",
    "aggʷaṭ", "leggʷam", "aggʷam", "neggʷam",
    "aḍebbʷaɣ", "afeggʷag", "asekkʷin", "tasekkʷint",
    "abeddʷil", "aneddʷal", "abelɣʷan", "asemmʷeḍ",
    "yeggʷrakken", "gʷakken", "bbʷadda", "ddʷakken",
]

# Quelques mots avec ᵒ (notation alternative)
WORDS_O = [
    "akᵒer", "ameqqᵒran", "nekkᵒni", "aẓekkᵒa",
    "azeggᵒaɣ", "yebbᵒi", "yeggᵒra",
]

# Phrases contextuelles avec ʷ
PHRASES_W = [
    "Ameqqʷran n tmurt-nneɣ d ameqqʷran.",
    "Yenna-yas : akʷer-d aɣrum!",
    "Ireggʷel si taddart-is.",
    "Azeggʷaɣ d ini ameqqʷran.",
    "Nekkʷni d Imaziɣen, nekkʷni d imezdaɣ n tmurt.",
    "Aggʷad n lmut yeggʷra-d s ufus-is.",
    "Yebbʷi-d tamment seg taddart-nneɣ.",
    "Tibbʷin-is d tibbʷin n ddunit.",
    "Yeţţebbʷa-yak-d lexṛif.",
    "Yemmʷet umcic-nni aseggʷas-agi.",
    "Temmʷet tmeṭṭut-nni tamuɣrist.",
    "Aggʷaṭ ameqqʷran i yezgan di tmurt.",
    "Aẓekkʷa ad nerreẓ neɣ ad nembeddʷal.",
    "Asemmʷeḍ ameqqʷran yekka-d seg ugafa.",
    "Tasekkʷint tameqqʷrant n taddart.",
]


def main():
    input_file = os.path.join(SCRIPT_DIR, "lignes_tamazight_v4.txt")
    output_file = os.path.join(SCRIPT_DIR, "lignes_tamazight_v5.txt")

    # Lire le corpus v4
    with open(input_file, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    print(f"📄 Corpus v4 : {len(lines)} lignes")
    print(f"   ʷ présents : {sum(1 for l in lines if 'ʷ' in l)}")

    # Ajouter les phrases avec ʷ (répéter pour avoir ~500 occurrences)
    new_lines = []

    # 1. Phrases contextuelles (répéter 20x = ~300 lignes)
    for _ in range(20):
        new_lines.extend(PHRASES_W)

    # 2. Générer des lignes mixtes avec les mots ʷ
    for _ in range(200):
        # Combiner 2-4 mots avec ʷ + quelques mots normaux
        n_words = random.randint(3, 7)
        words = []
        for _ in range(n_words):
            if random.random() < 0.5:
                words.append(random.choice(WORDS_W))
            else:
                # Piocher un mot normal du corpus existant
                random_line = random.choice(lines)
                random_words = random_line.split()
                if random_words:
                    words.append(random.choice(random_words))
        new_lines.append(" ".join(words))

    # 3. Quelques lignes avec ᵒ (notation alternative, moins fréquente)
    for _ in range(5):
        for w in WORDS_O:
            new_lines.append(f"{w} d awal ameqqʷran.")

    all_lines = lines + new_lines

    # Écrire le corpus v5
    with open(output_file, "w", encoding="utf-8") as f:
        for line in all_lines:
            f.write(line + "\n")

    # Stats
    w_count = sum(l.count("ʷ") for l in all_lines)
    o_count = sum(l.count("ᵒ") for l in all_lines)

    print(f"\n✅ Corpus v5 : {len(all_lines)} lignes")
    print(f"   ʷ occurrences : {w_count}")
    print(f"   ᵒ occurrences : {o_count}")
    print(f"   Écrit dans : {output_file}")


if __name__ == "__main__":
    random.seed(42)
    main()
