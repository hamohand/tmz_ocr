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

## Étape 3 : Lancer l'entraînement

Depuis le dossier `tesstrain/` (pas `training/`), vous lancerez la commande `make`.
Le but est d'utiliser le modèle Français (`fra`) comme base.

1. Téléchargez le modèle de base (`fra.traineddata` depuis `tessdata_best`) dans `tesstrain/data/fra/`.
2. Lancez l'entraînement :

```bash
cd tesstrain
make training MODEL_NAME=tmz_latn START_MODEL=fra TESSDATA=../data MAX_ITERATIONS=10000
```

*(Note : ces commandes peuvent nécessiter des ajustements selon votre OS. Consultez le [README officiel de Tesstrain](https://github.com/tesseract-ocr/tesstrain) pour les détails complets)*

## Étape 4 : Récupérer le modèle fini

Une fois l'entraînement terminé avec succès, un fichier `tmz_latn.traineddata` sera généré dans `tesstrain/data/tmz_latn/`.
Copiez ce fichier dans le dossier `../../models/` de la racine du projet.
