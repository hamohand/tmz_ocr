#!/usr/bin/env python3
"""
Renforcement des majuscules spéciales Tamazight dans le corpus.
Génère des phrases supplémentaires commençant par des majuscules spéciales
et contenant des noms propres avec ces caractères.

Objectif : équilibrer le ratio minuscules/majuscules pour l'entraînement OCR.
"""
import os
import re
import random

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPTS_DIR, "lignes_tamazight_enrichi.txt")
OUTPUT_FILE = os.path.join(SCRIPTS_DIR, "lignes_tamazight_v4.txt")

# Les 11 paires minuscule/majuscule Tamazight
CHAR_PAIRS = {
    'č': 'Č', 'ḍ': 'Ḍ', 'ǧ': 'Ǧ', 'ḥ': 'Ḥ', 'ɣ': 'Ɣ',
    'ṛ': 'Ṛ', 'ṣ': 'Ṣ', 'ṭ': 'Ṭ', 'ẓ': 'Ẓ', 'ɛ': 'Ɛ', 'ţ': 'Ţ',
}

# Noms propres kabyles avec majuscules spéciales (prénoms, lieux, etc.)
PROPER_NOUNS = {
    'Ḥ': ['Ḥamid', 'Ḥmed', 'Ḥnifa', 'Ḥmimi', 'Ḥend', 'Ḥsen', 'Ḥsissen', 'Ḥmida', 'Ḥadda'],
    'Ṭ': ['Ṭṭawes', 'Ṭiṭṭuc', 'Ṭawes', 'Ṭaleb', 'Ṭaher', 'Ṭaεkact'],
    'Ɣ': ['Ɣani', 'Ɣilas', 'Ɣezlan', 'Ɣiles'],
    'Ɛ': ['Ɛmer', 'Ɛli', 'Ɛziz', 'Ɛica', 'Ɛeddi', 'Ɛebdella', 'Ɛissa'],
    'Č': ['Čana', 'Čič', 'Čučen'],
    'Ḍ': ['Ḍaḥman', 'Ḍahbia'],
    'Ṣ': ['Ṣaliḥ', 'Ṣadek', 'Ṣaεdia'],
    'Ṛ': ['Ṛebbi', 'Ṛabeḥ', 'Ṛecid'],
    'Ẓ': ['Ẓiri', 'Ẓawit', 'Ẓeṛṛuq'],
    'Ǧ': ['Ǧamaε', 'Ǧurǧura'],
    'Ţ': ['Ţaqbaylit', 'Ţamaziɣt', 'Ţawes'],
}

# Phrases-patrons utilisant les noms propres (début de phrase avec majuscule)
PATTERNS = [
    "{name} yenna-d : « Azul fellawen ! »",
    "{name} yeffeɣ-d seg wexxam-is.",
    "{name} d argaz ameqqran.",
    "{name} d tameṭṭut tameqqrant.",
    "{name} yečča ṭṭam ɣef ṭṭabla.",
    "{name} yeẓra amɣar ɣef ubrid.",
    "{name} yettmeslay s teqbaylit.",
    "{name} yessawel-as i gma-s.",
    "{name} yekker-d ɣef ṣṣbeḥ.",
    "{name} yella di temdint.",
    "{name} yuɣ-d aman seg tala.",
    "{name} yettwali adrar-nni.",
    "{name} yezga deg wexxam.",
    "{name} yessen ad iger.",
    "Ass-a {name} yeffeɣ ɣer ssuq.",
    "Tura {name} yufa abrid-is.",
    "Ay {name}, anida telliḍ ?",
    "Wagi d {name}, d ameddakkel-iw.",
    "D {name} i d-yewwin lxir.",
    "Ɣur {name}, d amɣar n taddart.",
]

# Phrases commençant directement par les majuscules spéciales (sans nom propre)
UPPERCASE_STARTERS = {
    'Č': [
        "Čan-d ičemma n wass-nni.",
        "Čuč yeffeɣ-d seg umalu.",
        "Čara d čara, ihi d wagi.",
    ],
    'Ḍ': [
        "Ḍefreɣ abrid n taddart.",
        "Ḍenneɣ-t s ufus-iw.",
        "Ḍelleɣ-as aqeṛṛu ɣer deffir.",
    ],
    'Ǧ': [
        "Ǧurǧura d adrar ameqqran.",
        "Ǧǧiɣ-t weḥd-s.",
        "Ǧǧan-t ad yekk abrid-is.",
    ],
    'Ḥ': [
        "Ḥemleɣ tamurt-iw.",
        "Ḥkuɣ-d lḥikaya n zik.",
        "Ḥaca d nekk i issen tidet.",
    ],
    'Ɣ': [
        "Ɣef leḥsab, ur d-yusi ara.",
        "Ɣliɣ-d seg useklu.",
        "Ɣur-wen ad tettuɣ ara awal-iw.",
    ],
    'Ṛ': [
        "Ṛebbi yefka-d ṣṣeḥḥa.",
        "Ṛeḥmeɣ-as i yemma.",
        "Ṛuḥeɣ ɣer ssuq n lḥedd.",
    ],
    'Ṣ': [
        "Ṣṣbeḥ yekker-d fell-i.",
        "Ṣṣwab yella ɣur-s.",
        "Ṣber ay ul-iw, ad tafeḍ.",
    ],
    'Ṭ': [
        "Ṭṭfen-t deg ubrid.",
        "Ṭṭuɣ ayen yeḍran iḍelli.",
        "Ṭṭaq-is i tmeddit d uswir.",
    ],
    'Ẓ': [
        "Ẓriɣ-t deg usawen.",
        "Ẓriɣ dacu ara d-tiniḍ.",
        "Ẓer amek tetteḍ leḥwayeǧ-ik.",
    ],
    'Ɛ': [
        "Ɛinni-k ad tedduḍ d nekk.",
        "Ɛzizen fell-i medden.",
        "Ɛawneɣ-t mi i-d-yesteqsa.",
    ],
    'Ţ': [
        "Ţamaziɣt d tutlayt-nneɣ.",
        "Ţaqbaylit d tutlayt tameqqrant.",
        "Ţawes tenna-d awal-is.",
    ],
}

# Objectif : au moins N occurrences de chaque majuscule dans le corpus final
TARGET_MIN_UPPERCASE = 500


def count_uppercase_chars(text):
    """Compte les occurrences de chaque majuscule spéciale."""
    counts = {}
    for upper in CHAR_PAIRS.values():
        counts[upper] = text.count(upper)
    return counts


def generate_name_sentences(char_upper, count):
    """Génère des phrases avec des noms propres commençant par la majuscule."""
    sentences = []
    names = PROPER_NOUNS.get(char_upper, [])
    if not names:
        return sentences

    for _ in range(count):
        name = random.choice(names)
        pattern = random.choice(PATTERNS)
        sentence = pattern.format(name=name)
        sentences.append(sentence)
    return sentences


def generate_starter_sentences(char_upper, count):
    """Génère des phrases commençant par la majuscule spéciale."""
    starters = UPPERCASE_STARTERS.get(char_upper, [])
    if not starters:
        return []
    return [random.choice(starters) for _ in range(count)]


def capitalize_first_special(line):
    """Si une phrase commence par une minuscule spéciale, la met en majuscule."""
    if not line:
        return line
    first = line[0]
    for lower, upper in CHAR_PAIRS.items():
        if first == lower:
            return upper + line[1:]
    return line


def main():
    print("=" * 60)
    print("🔠 Renforcement des majuscules spéciales Tamazight")
    print("=" * 60)

    # 1. Lire le corpus existant
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        existing_lines = [l.strip() for l in f if l.strip()]
    existing_text = "\n".join(existing_lines)
    print(f"\n📂 Corpus source : {len(existing_lines)} lignes")

    # 2. Compter les majuscules actuelles
    current_counts = count_uppercase_chars(existing_text)
    print(f"\n📊 Majuscules actuelles :")
    for char, count in sorted(current_counts.items(), key=lambda x: x[1]):
        deficit = max(0, TARGET_MIN_UPPERCASE - count)
        status = "✅" if count >= TARGET_MIN_UPPERCASE else f"⚠️ besoin de +{deficit}"
        print(f"   {char} : {count:>5} {status}")

    # 3. Générer des phrases supplémentaires
    new_lines = []

    for char_upper, current_count in current_counts.items():
        if current_count >= TARGET_MIN_UPPERCASE:
            continue

        needed = TARGET_MIN_UPPERCASE - current_count
        print(f"\n🔧 {char_upper} : besoin de {needed} occurrences supplémentaires")

        # a) Phrases avec noms propres
        name_sentences = generate_name_sentences(char_upper, needed // 2)
        new_lines.extend(name_sentences)
        print(f"   + {len(name_sentences)} phrases avec noms propres")

        # b) Phrases commençant par la majuscule
        starter_sentences = generate_starter_sentences(char_upper, needed // 2)
        new_lines.extend(starter_sentences)
        print(f"   + {len(starter_sentences)} phrases-amorce")

    # 4. Capitaliser certaines lignes existantes qui commencent par une minuscule spéciale
    capitalized = []
    for line in existing_lines:
        if line and line[0] in CHAR_PAIRS:
            cap_line = capitalize_first_special(line)
            if cap_line != line:
                capitalized.append(cap_line)
    # Limiter pour ne pas trop gonfler
    random.shuffle(capitalized)
    capitalized = capitalized[:500]
    new_lines.extend(capitalized)
    print(f"\n🔄 + {len(capitalized)} lignes existantes capitalisées")

    # 5. Écrire le corpus v4
    all_lines = existing_lines + new_lines
    random.shuffle(all_lines)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for line in all_lines:
            f.write(line + "\n")

    # 6. Vérification finale
    final_text = "\n".join(all_lines)
    final_counts = count_uppercase_chars(final_text)
    print(f"\n📊 Résultat final ({len(all_lines)} lignes) :")
    for char, count in sorted(final_counts.items(), key=lambda x: -x[1]):
        delta = count - current_counts[char]
        print(f"   {char} : {count:>5} (+{delta})")

    print(f"\n💾 Corpus v4 écrit : {OUTPUT_FILE}")
    print(f"   {len(all_lines)} lignes ({len(new_lines)} nouvelles)")
    print(f"\n✅ Terminé !")


if __name__ == "__main__":
    main()
