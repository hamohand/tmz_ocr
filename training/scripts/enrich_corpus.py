"""
Script pour enrichir le corpus en surreprésentant les phrases contenant
des caractères spécifiques au Tamazight Latin.

Les lettres latines standard (a-z) sont déjà bien reconnues grâce au modèle
français de base. Ce script multiplie les phrases contenant les caractères
spéciaux pour forcer le modèle à mieux les apprendre.
"""
import os
import re
from collections import Counter

# Caractères spécifiques au Tamazight Latin (non présents en français standard)
SPECIAL_CHARS = set("ḍṭṣẓṛḥɛɣčğεԐƐɛƔ")

# Caractères "rares" qui méritent une surreprésentation encore plus forte
RARE_CHARS = set("ɛɣƔԐεčğ")

INPUT_FILE = "lignes_tamazight.txt"
OUTPUT_FILE = "lignes_tamazight_enrichi.txt"

# Facteur de multiplication
MULTIPLY_SPECIAL = 3   # Phrases avec caractères spéciaux (ḍ, ṭ, etc.) → x3
MULTIPLY_RARE = 5      # Phrases avec caractères rares (ɛ, ɣ, č, etc.) → x5


def count_special_chars(line):
    """Compte les caractères spéciaux Tamazight dans une ligne."""
    return sum(1 for c in line if c in SPECIAL_CHARS)


def has_rare_chars(line):
    """Vérifie si la ligne contient des caractères rares."""
    return any(c in RARE_CHARS for c in line)


def analyze_corpus(lines):
    """Analyse la distribution des caractères spéciaux dans le corpus."""
    char_counts = Counter()
    lines_with_special = 0
    lines_with_rare = 0

    for line in lines:
        has_special = False
        has_rare = False
        for c in line:
            if c in SPECIAL_CHARS:
                char_counts[c] += 1
                has_special = True
            if c in RARE_CHARS:
                has_rare = True
        if has_special:
            lines_with_special += 1
        if has_rare:
            lines_with_rare += 1

    return char_counts, lines_with_special, lines_with_rare


def main():
    script_dir = os.path.dirname(__file__)
    input_path = os.path.join(script_dir, INPUT_FILE)
    output_path = os.path.join(script_dir, OUTPUT_FILE)

    with open(input_path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    print(f"=== Enrichissement du corpus Tamazight ===")
    print(f"Corpus original: {len(lines)} phrases")
    print()

    # Analyse avant
    char_counts, n_special, n_rare = analyze_corpus(lines)
    print("Distribution des caractères spéciaux (avant) :")
    for char, count in sorted(char_counts.items(), key=lambda x: -x[1]):
        print(f"  '{char}' : {count} occurrences")
    print(f"\n  Phrases avec car. spéciaux: {n_special}/{len(lines)} ({100*n_special//len(lines)}%)")
    print(f"  Phrases avec car. rares:    {n_rare}/{len(lines)} ({100*n_rare//len(lines)}%)")
    print()

    # Enrichissement
    enriched = []
    stats = {"normal": 0, "special": 0, "rare": 0}

    for line in lines:
        if has_rare_chars(line):
            # Caractères rares → multiplier fortement
            for _ in range(MULTIPLY_RARE):
                enriched.append(line)
            stats["rare"] += 1
        elif count_special_chars(line) > 0:
            # Caractères spéciaux → multiplier
            for _ in range(MULTIPLY_SPECIAL):
                enriched.append(line)
            stats["special"] += 1
        else:
            # Phrases standard → garder une seule fois
            enriched.append(line)
            stats["normal"] += 1

    print(f"Résultat de l'enrichissement :")
    print(f"  Phrases normales (x1):     {stats['normal']}")
    print(f"  Phrases spéciales (x{MULTIPLY_SPECIAL}):   {stats['special']} → {stats['special'] * MULTIPLY_SPECIAL} lignes")
    print(f"  Phrases rares (x{MULTIPLY_RARE}):      {stats['rare']} → {stats['rare'] * MULTIPLY_RARE} lignes")
    print(f"\n  Total corpus enrichi: {len(enriched)} lignes")

    # Analyse après
    char_counts_after, _, _ = analyze_corpus(enriched)
    print("\nDistribution des caractères spéciaux (après) :")
    for char, count in sorted(char_counts_after.items(), key=lambda x: -x[1]):
        before = char_counts.get(char, 0)
        ratio = count / before if before else 0
        print(f"  '{char}' : {before} → {count} (x{ratio:.1f})")

    # Sauvegarder
    with open(output_path, "w", encoding="utf-8") as f:
        for line in enriched:
            f.write(line + "\n")

    print(f"\nSauvegardé dans: {output_path}")
    print(f"\nPour régénérer les images : python generate_gt.py --corpus {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
