# Guide Technique : Workflow d'Entraînement avec Tesstrain

Ce document explique plus en détail le fonctionnement du dossier `/training` et le workflow pour créer `tmz_latn.traineddata`.

## Le Répertoire `tesstrain`

C'est un sous-module (cloné de `https://github.com/tesseract-ocr/tesstrain`). C'est le cœur du système. Il utilise un énorme `Makefile` pour orchestrer l'entraînement des réseaux de neurones (LSTM) de Tesseract.

## Le concept de "Ground Truth" (Vérité Terrain)

Pour que Tesseract apprenne, il lui faut des paires d'images et de textes parfaitement alignés, appelés "Ground Truth" (GT).

- **Format attendu** : Pour chaque ligne de texte, il faut 2 fichiers :
  - `ma_ligne_1.tif` (L'image de la ligne)
  - `ma_ligne_1.gt.txt` (Le fichier texte contenant *exactement* les caractères présents dans l'image).

- **Quantité** : Pour du fine-tuning, il faut viser au minimum plusieurs centaines, voire plusieurs milliers de paires (ex: 5000 lignes) couvrant tous les mots et caractères spéciaux.

- **Où les mettre ?** : Tous ces fichiers iront dans `C:\Users\hamoh\Documents\travail\tmz\tmz_ocr\training\data\tmz_latn-ground-truth\`.

## Les Outils de génération de Ground Truth

Créer ces milliers d'images à la main est impossible. Deux méthodes principales existent :

### Méthode 1 : OCR synthétique (Automatisée)
C'est la méthode recommandée pour démarrer. Vous prenez un fichier contenant des centaines de milliers de phrases en Tamazight (sans images). Vous utilisez un script qui va lire chaque phrase, choisir aléatoirement une police Amazigh (dans `/training/data/fonts`), dessiner l'image virtuelle de la phrase, et enregistrer les deux briques (`.tif` et `.gt.txt`).

*Note: Je peux coder ce script Python pour vous si vous fournissez un gros fichier de texte brut.*

### Méthode 2 : Découpage de documents existants
Si vous possédez de vrais documents scannés, vous devrez utiliser des outils comme `jTessBoxEditor` ou des scripts pour recadrer manuellement et transcrire chaque ligne.

## Déroulé de l'Entraînement 

Une fois les données dans le dossier `tmz_latn-ground-truth/`, vous vous placez dans `/training/tesstrain` via un terminal Linux (ou WSL, car `tesstrain` nécessite bash/make).

1. **Génération du fichier UNICHARSET** : L'outil scanne vos `gt.txt` et fait l'inventaire de *toutes* les lettres utilisées : a, b, c... ɛ, ɣ, etc.
2. **Extraction des modèles existants** : L'outil va ouvrir le modèle `fra.traineddata` pour récupérer le réseau de neurones pré-entraîné du français.
3. **Apprentissage LSTM** : Il envoie vos images à la boucle, vérifie ce que le modèle devine, le compare à la vérité terrain, puis corrige les poids du réseau (Les "Iterations"). Ceci est l'étape la plus longue (des heures ou des jours selon le CPU/GPU).
4. **Combinaison** : L'outil referme le réseau neuronal avec le nouvel unicharset dans le fichier final `tmz_latn.traineddata`.
