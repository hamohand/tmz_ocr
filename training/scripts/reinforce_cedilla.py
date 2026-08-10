"""
Script de renforcement spécifique pour distinguer :
  ţ (t + cédille) — son courant en kabyle
  ṭ (t + point souscrit) — son différent

Le défi : ces deux lettres sont visuellement très proches.
Stratégie : créer des paires contrastives (même mot avec ţ puis ṭ)
pour forcer le modèle à apprendre la différence.
"""
import os
import random

SCRIPT_DIR = os.path.dirname(__file__)
INPUT_CORPUS = os.path.join(SCRIPT_DIR, "lignes_tamazight_renforce.txt")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "lignes_tamazight_v3.txt")

# Mots réels avec ţ (cédille) extraits du corpus + ajouts courants en kabyle
WORDS_WITH_T_CEDILLA = [
    "ţxil-k", "ţxil", "yeţţaken", "tseţţeḍ", "teţţaked",
    "iţţamen", "yeţţawi", "Neţţidir", "Aţan", "ţzillimeɣ",
    "ţnadiɣ", "ţkel", "ţawil", "ţaneggarut", "ţ-nekker",
    "yeţṛajun", "yeţţaɣ", "neţţaṭṭaf", "yeţţekka", "teţţaruḍ",
    "yeţţuɣal", "neţţmeslay", "yeţţwaḥsab", "iţţuneḥsab",
    "ţţun", "Ţţun", "yeţţruẓu", "yeţţekkil", "ţamurt",
    "neţţhenni", "yeţţwali", "meţţa", "ţţuḥbibeɣ",
    "iţij", "Iţij", "yeţţili", "teţţili", "neţţili",
    "ţella", "ţekker", "ţuɣal", "ţafat",
]

# Mots réels avec ṭ (point souscrit) pour contraste
WORDS_WITH_T_DOT = [
    "ṭṭṣeɣ", "nɛeṭṭel", "tɛeṭṭleḍ", "tameṭṭut",
    "yeṭṭeṣ", "yeṭṭef", "neṭṭef", "iṭij", "aṭas",
    "teṭṭeṣ", "yettwaṭṭef", "meṭṭawet", "aṭan", "yeṭṭfeḍ",
    "taṭṭuft", "isseṭṭif", "ṭṭfeɣ", "yewweṭ", "ṭṭwaleɣ",
    "leṭyur", "amuṭṭan",
]

# Mots courants neutres
COMMON_WORDS = [
    "nekk", "netta", "nettat", "kečč", "kemm",
    "d", "n", "i", "la", "ur", "ad", "ara",
    "yella", "tella", "llan", "yebɣa", "yewwi",
    "axxam", "argaz", "taqcict", "tamurt",
    "deg", "ɣer", "seg", "fell-as", "akked",
    "tura", "iḍelli", "azekka", "yal", "ass",
    "awal", "isem", "lxedma", "abrid", "adrar",
    "yenna", "tenna", "nnan", "qqaren",
]

NUM_CEDILLA_SENTENCES = 600      # Phrases avec ţ seul
NUM_DOT_SENTENCES = 200          # Phrases avec ṭ seul (rappel)
NUM_CONTRAST_SENTENCES = 400     # Phrases avec ţ ET ṭ ensemble
NUM_ISOLATION = 300              # Mots isolés avec ţ


def make_sentence(word_lists, min_w=3, max_w=6):
    """Génère une phrase avec des mots des listes fournies + mots courants."""
    n = random.randint(min_w, max_w)
    n_target = random.randint(1, min(3, n))
    words = []
    for _ in range(n_target):
        wl = random.choice(word_lists)
        words.append(random.choice(wl))
    for _ in range(n - n_target):
        words.append(random.choice(COMMON_WORDS))
    random.shuffle(words)
    s = " ".join(words)
    s = s[0].upper() + s[1:]
    if not s.endswith((".", "!", "?")):
        s += "."
    return s


def main():
    random.seed(123)

    with open(INPUT_CORPUS, "r", encoding="utf-8") as f:
        existing_lines = [l.strip() for l in f if l.strip()]

    print("=== Renforcement v3 : Distinguer ţ (cédille) de ṭ (point) ===")
    print(f"Corpus v2 : {len(existing_lines)} phrases")
    print()

    generated = []

    # 1. Phrases avec ţ (cédille) uniquement
    for _ in range(NUM_CEDILLA_SENTENCES):
        generated.append(make_sentence([WORDS_WITH_T_CEDILLA]))
    print(f"  ţ seul :     {NUM_CEDILLA_SENTENCES} phrases")

    # 2. Phrases avec ṭ (point) uniquement (rappel)
    for _ in range(NUM_DOT_SENTENCES):
        generated.append(make_sentence([WORDS_WITH_T_DOT]))
    print(f"  ṭ seul :     {NUM_DOT_SENTENCES} phrases")

    # 3. Phrases CONTRASTIVES : ţ ET ṭ dans la même phrase
    for _ in range(NUM_CONTRAST_SENTENCES):
        generated.append(make_sentence([WORDS_WITH_T_CEDILLA, WORDS_WITH_T_DOT]))
    print(f"  ţ + ṭ mix :  {NUM_CONTRAST_SENTENCES} phrases contrastives")

    # 4. Mots isolés avec ţ
    for _ in range(NUM_ISOLATION):
        generated.append(random.choice(WORDS_WITH_T_CEDILLA))
    print(f"  ţ isolés :   {NUM_ISOLATION} mots")

    # 5. Tripler les phrases existantes contenant ţ
    existing_with_cedilla = [l for l in existing_lines if "ţ" in l or "Ţ" in l]
    duplicated = existing_with_cedilla * 4
    generated.extend(duplicated)
    print(f"  Existantes ×4 : {len(existing_with_cedilla)} phrases × 4 = {len(duplicated)}")

    # 6. Paires contrastives directes (même structure, ţ vs ṭ)
    contrast_pairs = [
        ("Aţan d aṭan.", "Aţan ur yelli d aṭan."),
        ("Iţij yella deg igenni.", "Iṭij yella deg igenni."),
        ("Neţţidir tura.", "Neṭṭef tura."),
        ("Yeţţawi-d awal.", "YeṬṬef-d awal."),
        ("Meţţa d meṭṭawet.", "Meţţa ur d-meṭṭawet."),
        ("Teţţaked d tameṭṭut.", "Teţţaked yis-s."),
        ("Yeţţuɣal ɣer axxam.", "YeṭṭeṢ deg axxam."),
        ("Ţella tamurt.", "Ṭṭfeɣ tamurt."),
        ("Yeţţili d yeṭṭeṣ.", "Neţţili d neṭṭef."),
        ("ţxil ṭṭfeɣ", "ṭṭfeɣ ţxil"),
    ]
    for _ in range(50):
        for pair in contrast_pairs:
            generated.append(pair[0])
            generated.append(pair[1])
    print(f"  Paires contrastives : {len(contrast_pairs)} × 50 × 2 = {len(contrast_pairs) * 100}")

    # Assembler
    final = existing_lines + generated

    print(f"\n{'='*50}")
    print(f"  Corpus v2 :          {len(existing_lines):>6}")
    print(f"  Phrases ajoutées :   {len(generated):>6}")
    print(f"  TOTAL v3 :           {len(final):>6}")

    # Compter
    print(f"\nDistribution :")
    for char, name in [("ţ", "ţ (cédille)"), ("ṭ", "ṭ (point)"), ("Ţ", "Ţ maj")]:
        before = sum(l.count(char) for l in existing_lines)
        after = sum(l.count(char) for l in final)
        ratio = after / before if before > 0 else float('inf')
        print(f"  {name:15s} : {before:>5} → {after:>6}  (×{ratio:.1f})")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for line in final:
            f.write(line + "\n")

    print(f"\nSauvegardé : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
