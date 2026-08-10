#!/usr/bin/env python3
"""
Télécharge le dataset complet Sifal/Kabyle-French et fusionne avec le corpus local.
"""
import os, re, sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_WORDLIST = os.path.join(SCRIPTS_DIR, "..", "data", "tmz_latn.wordlist")
TMZ_SPECIAL = set("čḍǧḥɣṛṣṭẓɛţČḌǦḤƔṚṢṬẒƐŢ")
WORD_PATTERN = re.compile(
    r"^[a-zA-ZàâäéèêëïîôùûüÿçœæÀÂÄÉÈÊËÏÎÔÙÛÜŸÇŒÆčḍǧḥɣṛṣṭẓɛţČḌǦḤƔṚṢṬẒƐŢεԐ]"
    r"[a-zA-ZàâäéèêëïîôùûüÿçœæÀÂÄÉÈÊËÏÎÔÙÛÜŸÇŒÆčḍǧḥɣṛṣṭẓɛţČḌǦḤƔṚṢṬẒƐŢεԐ'\-]*$"
)

LOCAL_FILES = [
    os.path.join(SCRIPTS_DIR, "lignes_tamazight.txt"),
    os.path.join(SCRIPTS_DIR, "lignes_tamazight_enrichi.txt"),
    os.path.join(SCRIPTS_DIR, "lignes_tamazight_v3.txt"),
    os.path.join(SCRIPTS_DIR, "lignes_tamazight_renforce.txt"),
]

def extract_words(text):
    words = set()
    for token in re.split(r'[\s,;:!?.()\[\]{}"«»…\t\n]+', text):
        token = token.strip("'\"''""-–—_/\\|<>*+#@&=^~`")
        if token and len(token) >= 2 and WORD_PATTERN.match(token):
            words.add(token)
    return words

def main():
    print("=" * 60)
    print("🔤 Wordlist enrichie — corpus local + HuggingFace (115K)")
    print("=" * 60)

    # 1. Local
    print("\n📂 Corpus local...")
    local_words = set()
    for fp in LOCAL_FILES:
        if not os.path.exists(fp):
            continue
        with open(fp, "r", encoding="utf-8") as f:
            w = extract_words(f.read())
        print(f"  ✓ {os.path.basename(fp)} : {len(w)} mots")
        local_words.update(w)
    print(f"   → {len(local_words)} mots uniques locaux")

    # 2. HuggingFace — colonne kabyle = 'Ẓriɣ dacu ara d-tiniḍ.'
    print("\n📡 Téléchargement Sifal/Kabyle-French...")
    hf_words = set()
    try:
        from datasets import load_dataset
        ds = load_dataset("Sifal/Kabyle-French", split="train")
        print(f"   Dataset chargé : {len(ds)} lignes")

        # La colonne kabyle est la 2e (index 1 dans column_names)
        kab_col = ds.column_names[1]  # 'Ẓriɣ dacu ara d-tiniḍ.'
        print(f"   Colonne kabyle : '{kab_col}'")

        for i, row in enumerate(ds):
            text = row.get(kab_col, "")
            if isinstance(text, str) and text:
                hf_words.update(extract_words(text))
            if (i + 1) % 20000 == 0:
                print(f"   📥 {i+1}/{len(ds)} — {len(hf_words)} mots")

        print(f"   ✓ {len(ds)} phrases → {len(hf_words)} mots uniques")
    except Exception as e:
        print(f"   ❌ Erreur : {e}")
        import traceback
        traceback.print_exc()

    # 3. Fusion
    new_from_hf = hf_words - local_words
    all_words = local_words | hf_words
    print(f"\n🔀 Fusion :")
    print(f"   Local : {len(local_words)}")
    print(f"   HuggingFace : {len(hf_words)} ({len(new_from_hf)} nouveaux)")
    print(f"   Total : {len(all_words)} mots uniques")

    # 4. Écriture
    sorted_words = sorted(all_words, key=lambda w: w.lower())
    os.makedirs(os.path.dirname(OUTPUT_WORDLIST), exist_ok=True)
    with open(OUTPUT_WORDLIST, "w", encoding="utf-8") as f:
        for w in sorted_words:
            f.write(w + "\n")

    # 5. Stats
    with_special = sum(1 for w in sorted_words if any(c in TMZ_SPECIAL for c in w))
    char_freq = {}
    for w in sorted_words:
        for c in w:
            if c in TMZ_SPECIAL:
                char_freq[c] = char_freq.get(c, 0) + 1

    print(f"\n💾 Wordlist : {OUTPUT_WORDLIST}")
    print(f"   {len(sorted_words)} mots total")
    print(f"   {with_special} avec car. spéciaux ({100*with_special/len(sorted_words):.1f}%)")
    print(f"\n   Fréquence caractères spéciaux :")
    for char, count in sorted(char_freq.items(), key=lambda x: -x[1]):
        print(f"     {char} : {count}")
    print(f"\n✅ Terminé !")

if __name__ == "__main__":
    main()
