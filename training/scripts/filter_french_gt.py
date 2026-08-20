#!/usr/bin/env python3
"""
filter_french_gt.py — Filtre les lignes en français pur du GT réel.

Garde une ligne si elle contient au moins un caractère tamazight spécial.
Supprime les lignes purement en français (aucun caractère spécial + mots français courants).

Usage :
  python3 filter_french_gt.py [--dry-run]   # --dry-run pour voir sans supprimer
"""
import os
import sys
import re
import glob

REAL_GT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "real-scans-gt")

TMZ_SPECIAL = set("čḍǧḥɣṛṣṭẓɛţʷᵒČḌǦḤƔṚṢṬẒƐŢ")

# Mots-clés français très courants (absents du kabyle)
FRENCH_MARKERS = {
    "le", "la", "les", "de", "du", "des", "un", "une",
    "est", "et", "en", "que", "qui", "dans", "pour", "par",
    "avec", "sur", "au", "aux", "ce", "cette", "son", "sa",
    "ses", "leur", "leurs", "ou", "ne", "pas", "plus",
    "être", "avoir", "fait", "fait", "comme", "mais",
    "tout", "tous", "toute", "même", "aussi", "très",
    "bien", "peut", "faire", "dit", "dire", "voir",
    "bon", "bonne", "homme", "femme", "petit", "grand",
    "chez", "entre", "sous", "après", "avant", "sans",
    "donc", "car", "elle", "ils", "elles", "nous", "vous",
    "je", "tu", "il", "on", "se", "me", "te",
}


def classify_line(text):
    """Classifie une ligne : 'tmz' (garder), 'french' (supprimer), 'short' (supprimer)."""
    text = text.strip()

    if len(text) < 3:
        return "short"

    # Si un caractère tamazight spécial → garder
    if any(c in TMZ_SPECIAL for c in text):
        return "tmz"

    # Compter les mots français
    words = re.findall(r'[a-zA-ZàâäéèêëïîôùûüçÀÂÄÉÈÊËÏÎÔÙÛÜÇ]+', text.lower())
    if not words:
        return "short"

    french_count = sum(1 for w in words if w in FRENCH_MARKERS)
    french_ratio = french_count / len(words)

    # Si plus de 30% de mots français courants → c'est du français
    if french_ratio > 0.3 and len(words) >= 3:
        return "french"

    # Si aucun caractère spécial et la plupart des mots sont des mots courants en français
    if french_ratio > 0.2 and french_count >= 2:
        return "french"

    # Sinon, garder (pourrait être du kabyle sans diacritiques)
    return "maybe_tmz"


def main():
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("🔍 Mode dry-run — aucun fichier ne sera supprimé\n")

    gt_files = sorted(glob.glob(os.path.join(REAL_GT_DIR, "*.gt.txt")))

    if not gt_files:
        print(f"❌ Aucun fichier .gt.txt dans {REAL_GT_DIR}")
        sys.exit(1)

    stats = {"tmz": 0, "maybe_tmz": 0, "french": 0, "short": 0}
    to_remove = []
    examples = {"tmz": [], "french": [], "maybe_tmz": []}

    for gt_file in gt_files:
        with open(gt_file, "r", encoding="utf-8") as f:
            text = f.read().strip()

        category = classify_line(text)
        stats[category] += 1

        basename = os.path.basename(gt_file).replace(".gt.txt", "")

        if category in ("french", "short"):
            to_remove.append(basename)
            if category == "french" and len(examples["french"]) < 10:
                examples["french"].append(f"  ❌ {text[:80]}")
        else:
            if len(examples.get(category, [])) < 5:
                examples.setdefault(category, []).append(f"  ✅ {text[:80]}")

    # Afficher les statistiques
    total = sum(stats.values())
    print("=" * 60)
    print(f"📊 Classification des {total} lignes GT réelles")
    print("=" * 60)
    print(f"  ✅ Tamazight (car. spéciaux)  : {stats['tmz']}")
    print(f"  ✅ Probablement Tamazight     : {stats['maybe_tmz']}")
    print(f"  ❌ Français pur               : {stats['french']}")
    print(f"  ❌ Trop court (< 3 car.)      : {stats['short']}")
    print(f"  ────────────────────────────────")
    print(f"  📁 À garder : {stats['tmz'] + stats['maybe_tmz']}")
    print(f"  🗑  À supprimer : {stats['french'] + stats['short']}")

    print(f"\n📝 Exemples de lignes FRANÇAISES supprimées :")
    for ex in examples["french"]:
        print(ex)

    print(f"\n📝 Exemples de lignes TAMAZIGHT gardées :")
    for ex in examples.get("tmz", []):
        print(ex)

    if not dry_run and to_remove:
        print(f"\n🗑  Suppression de {len(to_remove)} paires...")
        removed = 0
        for basename in to_remove:
            for ext in [".gt.txt", ".tif", ".png"]:
                path = os.path.join(REAL_GT_DIR, basename + ext)
                if os.path.exists(path):
                    os.remove(path)
                    removed += 1
        print(f"   ✅ {removed} fichiers supprimés")

        remaining = len(glob.glob(os.path.join(REAL_GT_DIR, "*.gt.txt")))
        print(f"   📁 {remaining} paires GT restantes")
    elif dry_run:
        print(f"\n💡 Relancez sans --dry-run pour appliquer les suppressions")


if __name__ == "__main__":
    main()
