# Ressources et Données

Ce document détaille les ressources utilisées pour l'entraînement du modèle OCR Tamazight.

## 📝 Corpus Textuel

### Corpus Original
- **Source** : Sifal/Kabyle-French, issu de Tatoeba (via Hugging Face).
- **Taille** : 4 913 phrases réelles en Kabyle.

### Corpus Enrichi (v4)
- **Taille** : 22 524 lignes avec renforcement des caractères spéciaux majuscules. Chaque caractère majuscule spécial apparaît environ 500 fois.
- **Scripts utilisés** :
  - `reinforce_uppercase.py` : Renforcement spécifique des majuscules.
  - `enrich_corpus.py`, `reinforce_cedilla.py`, `reinforce_weak_chars.py` pour les autres caractères.

## 📝 Wordlist et Fichiers de Configuration
- **Wordlist** : 78 203 mots uniques extraits du corpus HuggingFace Sifal/Kabyle-French (115K phrases). Construite avec `build_wordlist_hf.py` et `build_wordlist.py`.
- **Fichiers de ponctuation et chiffres** : `tmz_latn.punc` (19 caractères) et `tmz_latn.numbers` (10 chiffres).

## 🖼 Ground Truth (Images + Texte)

- **Volume total** : 22 523 images augmentées (`.tif` + `.gt.txt`).
- **Data Augmentation** : 9 transformations appliquées (bruit Gaussien, rotation, flou, contraste, luminosité, arrière-plans texturés, tailles de polices variables, etc.) pour rendre le modèle plus robuste aux scans réels.

## 🔤 Polices (Fonts)

11 polices au total ont été utilisées pour la génération du Ground Truth, garantissant une bonne diversité typographique pour le modèle :
- 3 polices Google Noto Sans.
- 8 polices système standard.

## 🔠 Alphabet et Caractères Spéciaux

Le modèle prend en charge l'alphabet latin enrichi utilisé pour le Tamazight. Une attention particulière a été portée sur les 22 caractères spéciaux suivants (11 paires min/maj) :
**č/Č, ḍ/Ḍ, ǧ/Ǧ, ḥ/Ḥ, ɣ/Ɣ, ṛ/Ṛ, ṣ/Ṣ, ṭ/Ṭ, ẓ/Ẓ, ɛ/Ɛ, ţ/Ţ**

## 🤖 Modèle de Base et Modèle de Comparaison
- L'entraînement v4 a été réalisé en *fine-tuning* (2ème passe) à partir du modèle `tmz_latn` de la v3 (et non plus depuis le français). Le modèle fait environ 4.0 MB.
- **Modèle `kab`** : Le modèle de Bouaziz Ait Driss a été intégré pour comparaison. Tests sur 6 scans réels (Tagrest urɣu, Times d waman, Tawaɣit tayri, Amdan taggezt) : 87.6% de confiance pour le modèle v4, qui surpasse le modèle `kab` sur 4 pages sur 6.
