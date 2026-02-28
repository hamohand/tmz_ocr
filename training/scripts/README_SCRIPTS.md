# Utilisation de `generate_gt.py`

Ce script Python permet de générer instantanément des centaines d'images d'entraînement (Ground Truth) pour Tesseract OCR à partir d'un simple fichier texte.

## Prérequis

1. Installez la bibliothèque d'imagerie Python (Pillow) :
   ```bash
   pip install Pillow
   ```
2. Placez vos différentes polices Amazigh (fichiers `.ttf` ou `.otf`) dans le dossier `../data/fonts/`. Il en faut au moins une !
3. Remplissez le fichier `lignes_tamazight.txt` (qui sera créé à côté du script) avec une vraie phrase en tamazight **par ligne**.

## Exécution

Placez-vous dans le dossier `/training/scripts` et lancez :

```bash
python generate_gt.py
```

Le script va :
1. Lire chaque ligne de votre texte.
2. Choisir une police au hasard parmi celles disponibles.
3. Dessiner la phrase sur fond blanc.
4. Créer un fichier `.tif` et un `.gt.txt` correspondant dans `/training/data/tmz_latn-ground-truth/`.

Une fois ceci terminé, vous serez prêt à lancer `make training` dans le dossier `tesstrain`.
