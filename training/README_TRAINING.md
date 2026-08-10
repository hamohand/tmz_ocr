# Guide d'entraînement Tesseract pour l'Amazigh Latin (tmz_latn)

Nous utilisons l'outil officiel `tesstrain` pour faire du "fine-tuning" (affiner un modèle existant, comme le français ou l'anglais, pour lui apprendre les caractères amazighs).

## Prérequis Système

Vous aurez besoin d'installer :
- `tesseract-ocr` (et les bibliothèques de développement `libtesseract-dev`)
- `python3`
- `make` (GNU Make)
- Les utilitaires Tesseract d'entraînement

Sur Ubuntu/Debian ou via WSL sur Windows :
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-fra tesseract-ocr-eng libtesseract-dev libleptonica-dev bc make unzip python3 python3-pip
```

## Étape 1 : Préparer les Polices (Fonts)

Placez vos polices d'écriture `.ttf` (celles utilisées pour écrire le Tamazight) dans le dossier `data/fonts/`.

## Étape 2 : Préparer les Textes (Ground Truth)

Le dossier `data/tmz_latn-ground-truth/` doit contenir des paires de fichiers :
- Une image d'une ligne de texte en amazigh (ex: `ligne_001.tif` ou `.png`)
- Un fichier texte avec la transcription EXACTE de cette ligne (ex: `ligne_001.gt.txt`)

*Astuce : `tesstrain` possède un script pour générer ces images automatiquement à partir d'un gros fichier texte et de vos polices.*

## Étape 3 : Préparer et Enrichir le Corpus

L'entraînement nécessite un corpus de bonne qualité. L'utilisation des scripts d'enrichissement (ex: `enrich_corpus.py` pour suréchantillonner les caractères spéciaux et rares, `reinforce_uppercase.py` pour garantir l'apprentissage des majuscules comme ţ/Ţ) est vivement conseillée (voir `scripts/README_SCRIPTS.md`).
À l'issue de cette étape, pour le modèle v4, un corpus de 22 524 lignes a été rendu sous forme de 22 523 paires d'images transformées (avec augmentation de données : bruit, rotation, flou, etc.).

## Étape 3bis : Dictionnaire de mots (Wordlist)

Pour améliorer la précision linguistique, nous utilisons un dictionnaire généré (`build_wordlist_hf.py` / `build_wordlist.py`) contenant 78 203 mots uniques, ainsi que des fichiers de ponctuation (`tmz_latn.punc`) et de nombres (`tmz_latn.numbers`) créés via `create_lang_files.sh`. Ces fichiers sont intégrés dans le modèle final.

## Étape 4 : Optimisation WSL et Système de Fichiers

> [!TIP]
> **Performance WSL** : Pour de meilleures performances I/O (très importantes pour l'entraînement), il est fortement recommandé de placer le dossier de `tesstrain` sur le système de fichiers natif de WSL (ex: `/home/hamoh/tmz_training/tesstrain/`) plutôt que sur le point de montage `/mnt/c/`. Vous pouvez utiliser la méthode du 'tar pipe' pour transférer rapidement vos données générées de Windows vers WSL.

## Étape 5 : Lancer l'entraînement

> [!WARNING]
> **Attention Modèle de Base** : Le modèle pré-entraîné `fra.traineddata` utilisé comme point de départ (`START_MODEL`) **DOIT absolument être la version FLOAT (best)** issue du dépôt [tessdata_best](https://github.com/tesseract-ocr/tessdata_best/raw/main/fra.traineddata).
> Ne **PAS** utiliser la version 'fast' (entière) qui s'installe par défaut via `apt-get install tesseract-ocr-fra`, car elle est incompatible avec le fine-tuning et provoquera des erreurs.

1. Téléchargez la bonne version de `fra.traineddata` (float) et placez-la dans votre répertoire `TESSDATA`, par exemple `/home/hamoh/tmz_training/tesstrain/data/tessdata_best`.
2. Lancez l'entraînement depuis votre dossier `tesstrain` Linux natif. 
   **Note sur le 2nd Pass Fine-Tuning** : Pour la v4, nous avons utilisé notre modèle `tmz_latn` v3 existant comme point de départ au lieu du français.

```bash
cd /home/hamoh/tmz_training/tesstrain/
make training MODEL_NAME=tmz_latn START_MODEL=tmz_latn TESSDATA=/home/hamoh/tmz_training/tesstrain/data/tessdata_best MAX_ITERATIONS=20000
```

*(Note : ces commandes peuvent nécessiter des ajustements selon votre OS. Consultez le [README officiel de Tesstrain](https://github.com/tesseract-ocr/tesstrain) pour les détails complets)*

### Résultats Attendus (Modèle v4)
- **Itérations** : 19 000 au total (meilleur checkpoint atteint à l'itération 5 420).
- **BCER** (Character Error Rate) : 0.989%
- **BWER** (Word Error Rate) : 3.000%
## Étape 6 : Récupérer le modèle fini

Une fois l'entraînement terminé avec succès, un fichier `tmz_latn.traineddata` sera généré dans `tesstrain/data/tmz_latn/`.
Copiez ce fichier dans le dossier `../../models/` de la racine du projet.
