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

- **`enrich_corpus.py`** : Ce script enrichit le corpus en suréchantillonnant les caractères spéciaux (x3) et les caractères très rares (x5). Lors de la version v3, le corpus enrichi a atteint 18 055 lignes.
- **`reinforce_cedilla.py`** : Renforce spécifiquement l'apparition des caractères avec cédille.
- **`reinforce_weak_chars.py`** : Cible et renforce les autres caractères "faibles" (ceux où l'OCR a historiquement du mal).

## 3. `generate_gt.py`
Une fois le corpus préparé et enrichi, ce script génère les images et fichiers textes (Ground Truth) associés.

### Exécution :
```bash
python generate_gt.py
```

Le script va :
1. Lire chaque ligne de votre texte (ex: 18 055 lignes).
2. Choisir une police au hasard parmi celles disponibles.
3. Dessiner la phrase sur fond blanc.
4. Créer un fichier `.tif` et un `.gt.txt` correspondant dans le dossier de destination (ex: 13 711 paires générées pour la v3).

*Note : Lors de la génération de la v3, le fichier généré `tmz_latn_9586` était corrompu et doit être exclu de l'entraînement.*

Une fois ces paires prêtes et transférées (idéalement sur le système de fichiers natif WSL pour des raisons de performance), vous êtes prêt pour l'entraînement.
