# Scripts de Préparation et d'Entraînement

Ce dossier contient divers scripts Python permettant de préparer le corpus, l'enrichir et générer la vérité terrain (Ground Truth) pour l'entraînement de Tesseract OCR.

## Prérequis

1. Installez la bibliothèque d'imagerie Python (Pillow) :
   ```bash
   pip install Pillow
   ```
2. Placez vos différentes polices Amazigh (fichiers `.ttf` ou `.otf`) dans le dossier `../data/fonts/`.

# Scripts de Préparation et d'Entraînement

Ce dossier contient divers scripts Python permettant de préparer le corpus, l'enrichir et générer la vérité terrain (Ground Truth) pour l'entraînement de Tesseract OCR.

## Prérequis

1. Installez la bibliothèque d'imagerie Python (Pillow) :
   ```bash
   pip install Pillow
   ```
2. Placez vos différentes polices Amazigh (fichiers `.ttf` ou `.otf`) dans le dossier `../data/fonts/`.

## 1. `download_corpus.py`
Ce script permet de télécharger le texte brut (corpus) qui servira de base à l'entraînement. Il prépare le fichier initial de lignes en tamazight.

## 2. L'Enrichissement du Corpus
Avant de générer les images, il est crucial de s'assurer que le modèle verra suffisamment de caractères rares ou spécifiques.

- **`enrich_corpus.py`** : Ce script enrichit le corpus en suréchantillonnant les caractères spéciaux (x3) et les caractères très rares (x5).
- **`reinforce_cedilla.py`** : Renforce spécifiquement l'apparition des caractères avec cédille.
- **`reinforce_weak_chars.py`** : Cible et renforce les autres caractères "faibles" (ceux où l'OCR a historiquement du mal).
- **`reinforce_uppercase.py`** : Assure qu'il y a au moins 500 occurrences de chaque caractère spécial majuscule (ex: Ţ).

## 2.1 Dictionnaire et Modèles Linguistiques (Wordlist)

- **`build_wordlist.py` / `build_wordlist_hf.py`** : Scrape ou utilise l'API Hugging Face pour construire un dictionnaire massif (78 203 mots uniques en v4).
- **`create_lang_files.sh`** : Crée les fichiers `tmz_latn.punc` et `tmz_latn.numbers` requis pour la construction du modèle linguistique final avec `combine_lang_model`.

## 2.2 Utilitaires de Test

- **`test_compare.py`** : Permet de comparer notre modèle avec un autre (ex: le modèle `kab` de Bouaziz Ait Driss).
- **`inspect_ds.py`** / **`test_augment.py`** : Scripts pour vérifier la structure du jeu de données et tester visuellement les augmentations d'images.

## 3. `generate_gt.py`
Une fois le corpus préparé et enrichi, ce script génère les images et fichiers textes (Ground Truth) associés, avec support de l'**Augmentation de Données** (`AUGMENT_ENABLED`). Le script applique 9 transformations différentes (bruit, poivre & sel, rotation, flou, contraste, luminosité, fonds texturés, variation de tailles, couleurs de texte).

### Exécution :
```bash
python generate_gt.py
```

Le script va :
1. Lire chaque ligne de votre texte (ex: 22 524 lignes).
2. Choisir une police au hasard parmi celles disponibles.
3. Appliquer des transformations si l'augmentation est activée.
4. Créer un fichier `.tif` et un `.gt.txt` correspondant dans le dossier de destination (22 523 paires générées pour la v4).

*Note : Lors de la génération des précédentes versions, certains fichiers corrompus étaient exclus de l'entraînement. Les tests d'intégrité intégrés évitent ce problème.*

Une fois ces paires prêtes et transférées (idéalement sur le système de fichiers natif WSL pour des raisons de performance), vous êtes prêt pour l'entraînement.
