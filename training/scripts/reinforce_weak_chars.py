"""
Script de génération de phrases synthétiques ciblant les 5 caractères Tamazight
les plus faibles en reconnaissance OCR :

  ṣ (0%)   ṭ (37%)   ǧ (12%)   ɛ (0%)   Ɛ (0%)

Stratégie :
1. Extraire les mots réels contenant ces caractères depuis le corpus existant
2. Générer des phrases synthétiques en combinant ces mots avec des mots courants
3. Ajouter des lignes isolées pour forcer l'apprentissage caractère par caractère
"""
import os
import random
import re

SCRIPT_DIR = os.path.dirname(__file__)
INPUT_CORPUS = os.path.join(SCRIPT_DIR, "lignes_tamazight.txt")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "lignes_tamazight_renforce.txt")

# Les 5 caractères faibles + leurs majuscules
WEAK_CHARS = set("ṣṭǧɛƐƔ")

# Mots réels contenant ces caractères (extraits du corpus + ajouts)
WORDS_WITH_S_DOT = [
    "ṣṣeḥ", "ṣṣeḥḥa", "ṣṣut", "ṣṣfa", "ṣṣerf", "ṣṣbeḥ",
    "ḥṣiɣ", "txelleṣ", "xuṣṣeɣ", "yettqeṣṣir", "y-iṣebbren",
    "taṣebḥit", "Tṣubb", "Nṣubb", "aṣebbiy", "ṣṣenεa",
    "ttexxiṣ", "imeṣlayen", "Ṣṣber", "iṣebbren",
    "tamṣalt", "ṣṣwab", "ṭṭṣeɣ", "ṣṣuḍ", "leṣlaḥ",
]

WORDS_WITH_T_DOT = [
    "ṭṭṣeɣ", "nɛeṭṭel", "tɛeṭṭleḍ", "tameṭṭut",
    "yeṭṭeṣ", "yeṭṭef", "neṭṭef", "iṭij", "aṭas",
    "teṭṭeṣ", "yettwaṭṭef", "meṭṭawet", "aṭan", "yeṭṭfeḍ",
    "taṭṭuft", "tameṭṭut-a", "isseṭṭif", "ṭṭfeɣ",
    "leṭyur", "amuṭṭan", "yewweṭ", "ṭṭwaleɣ",
]

WORDS_WITH_G_CARON = [
    "Werǧin", "werǧin", "Urǧin", "yeǧǧa", "ttaǧǧa",
    "lǧal", "Eǧǧ-iyi", "Eǧǧ", "ǧǧeɣ", "ǧahennama",
    "uḥwaǧeɣ", "tuḥwaǧeḍ", "yuḥwaǧen", "iǧehden",
    "izewǧen", "ttaǧa", "tjeǧǧigin", "teǧǧeḍ", "teǧǧ",
    "zzwaǧ", "lmeǧlis", "ḥwaǧeɣ",
]

WORDS_WITH_EPSILON = [
    "ɛad", "ɛeddan", "ɛiwneɣ", "tesɛiḍ", "sɛiɣ", "Sɛiɣ",
    "yesɛa", "Yesɛa", "nesɛi", "yesɛi", "fqiɛeɣ",
    "Yuɛeṛ", "Iɛedda", "meɛna", "leɛqel", "zerreɛ",
    "tɛumeḍ", "Ɛad", "Ɛeẓẓen", "leɛyub", "ɛecrin",
    "Ur-ɛad", "albaɛḍ", "tɛeqqlem", "tɛeqqleḍ",
    "nɛeṭṭel", "tɛeṭṭleḍ", "sebɛa", "ṣṣenɛa",
    "nɛemmeḍ", "tɛedda", "yuɛer", "taɛzizt",
]

# Mots courants (neutres) pour construire des phrases
COMMON_WORDS = [
    "nekk", "netta", "nettat", "kečč", "kemm", "nutni",
    "d", "n", "i", "la", "ur", "ad", "ara",
    "yella", "tella", "llan", "yebɣa", "yewwi",
    "axxam", "argaz", "taqcict", "aqcic", "tamurt",
    "deg", "ɣer", "seg", "fell-as", "akked",
    "tura", "iḍelli", "azekka", "yal", "ass",
    "awal", "isem", "lxedma", "abrid", "adrar",
    "yenna", "tenna", "nnan", "qqaren",
]

# Connecteurs pour phrases plus naturelles
CONNECTORS = [
    "", "d", "la", "ur", "ad", "ara", "ɣef", "deg",
    "akked", "meɛna", "neɣ", "alamma",
]

NUM_SENTENCES_PER_CATEGORY = 500
NUM_ISOLATION_LINES = 200


def generate_mixed_sentence(target_words, min_words=3, max_words=7):
    """Génère une phrase mélangeant mots cibles et mots courants."""
    n = random.randint(min_words, max_words)
    # Au moins 1-2 mots cibles
    n_target = random.randint(1, min(3, n))
    n_common = n - n_target

    words = []
    for _ in range(n_target):
        words.append(random.choice(target_words))
    for _ in range(n_common):
        words.append(random.choice(COMMON_WORDS))

    random.shuffle(words)

    # Ajouter occasionnellement un connecteur
    if random.random() > 0.5 and len(words) > 2:
        pos = random.randint(1, len(words) - 1)
        conn = random.choice(CONNECTORS)
        if conn:
            words.insert(pos, conn)

    sentence = " ".join(words)
    # Majuscule au début, point à la fin
    sentence = sentence[0].upper() + sentence[1:]
    if not sentence.endswith((".", "!", "?")):
        sentence += "."

    return sentence


def generate_isolation_lines(chars_with_words):
    """
    Génère des lignes isolées avec un seul mot contenant le caractère cible.
    Force le modèle à reconnaître le caractère dans différents contextes.
    """
    lines = []
    for _ in range(NUM_ISOLATION_LINES):
        category = random.choice(list(chars_with_words.keys()))
        word = random.choice(chars_with_words[category])
        lines.append(word)
    return lines


def generate_multi_char_sentences(all_word_lists, count=200):
    """
    Génère des phrases contenant PLUSIEURS caractères faibles à la fois.
    Force le modèle à les distinguer dans un même contexte.
    """
    lines = []
    for _ in range(count):
        # Prendre des mots de 2-3 catégories différentes
        categories = random.sample(list(all_word_lists.keys()), min(3, len(all_word_lists)))
        target_words = []
        for cat in categories:
            target_words.append(random.choice(all_word_lists[cat]))

        # Ajouter 1-3 mots courants
        for _ in range(random.randint(1, 3)):
            target_words.append(random.choice(COMMON_WORDS))

        random.shuffle(target_words)
        sentence = " ".join(target_words)
        sentence = sentence[0].upper() + sentence[1:]
        if not sentence.endswith((".", "!", "?")):
            sentence += "."
        lines.append(sentence)

    return lines


def main():
    random.seed(42)

    # Charger le corpus existant
    with open(INPUT_CORPUS, "r", encoding="utf-8") as f:
        original_lines = [l.strip() for l in f if l.strip()]

    print("=== Renforcement du corpus pour les caractères faibles ===")
    print(f"Corpus original : {len(original_lines)} phrases")
    print()
    print("Caractères ciblés :")
    print("  ṣ (0% reconnaissance)   — Ajout de mots avec ṣ")
    print("  ṭ (37% reconnaissance)  — Ajout de mots avec ṭ")
    print("  ǧ (12% reconnaissance)  — Ajout de mots avec ǧ")
    print("  ɛ (0% reconnaissance)   — Ajout de mots avec ɛ")
    print("  Ɛ (0% reconnaissance)   — Ajout de mots avec Ɛ")
    print()

    all_word_lists = {
        "ṣ": WORDS_WITH_S_DOT,
        "ṭ": WORDS_WITH_T_DOT,
        "ǧ": WORDS_WITH_G_CARON,
        "ɛ": WORDS_WITH_EPSILON,
    }

    generated_lines = []

    # 1. Phrases ciblées par caractère
    for char_name, word_list in all_word_lists.items():
        sentences = []
        for _ in range(NUM_SENTENCES_PER_CATEGORY):
            sentences.append(generate_mixed_sentence(word_list))
        generated_lines.extend(sentences)
        print(f"  {char_name} : {len(sentences)} phrases générées (avec {len(word_list)} mots cibles)")

    # 2. Phrases multi-caractères (mix)
    multi_lines = generate_multi_char_sentences(all_word_lists, count=300)
    generated_lines.extend(multi_lines)
    print(f"  Mix : {len(multi_lines)} phrases avec plusieurs caractères faibles")

    # 3. Lignes d'isolation (mots seuls)
    iso_lines = generate_isolation_lines(all_word_lists)
    generated_lines.extend(iso_lines)
    print(f"  Isolation : {len(iso_lines)} mots isolés")

    # 4. Extraire et dupliquer les phrases existantes contenant ces caractères
    existing_weak = []
    for line in original_lines:
        if any(c in WEAK_CHARS for c in line):
            existing_weak.append(line)

    # Tripler les phrases existantes avec ces caractères
    duplicated = existing_weak * 3
    generated_lines.extend(duplicated)
    print(f"  Existantes x3 : {len(existing_weak)} phrases × 3 = {len(duplicated)}")

    # Assembler le corpus final
    final_corpus = original_lines + generated_lines

    print(f"\n{'='*50}")
    print(f"  Corpus original :    {len(original_lines):>6} phrases")
    print(f"  Phrases ajoutées :   {len(generated_lines):>6} phrases")
    print(f"  TOTAL :              {len(final_corpus):>6} phrases")

    # Compter les caractères faibles dans le nouveau corpus
    print(f"\nDistribution des caractères faibles :")
    for char in "ṣṭǧɛƐ":
        count_before = sum(1 for line in original_lines for c in line if c == char)
        count_after = sum(1 for line in final_corpus for c in line if c == char)
        ratio = count_after / count_before if count_before > 0 else float('inf')
        print(f"  '{char}' : {count_before:>5} → {count_after:>6}  (×{ratio:.1f})")

    # Sauvegarder
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for line in final_corpus:
            f.write(line + "\n")

    print(f"\nSauvegardé dans : {OUTPUT_FILE}")
    print(f"\nProchaines étapes :")
    print(f"  1. python generate_gt.py --corpus lignes_tamazight_renforce.txt")
    print(f"  2. wsl bash training/scripts/run_training.sh")


if __name__ == "__main__":
    main()
