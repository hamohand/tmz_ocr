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
C'est la méthode recommandée pour démarrer. Le processus complet (Pipeline) est le suivant :

1. **Téléchargement du Corpus** : Récupérer un grand volume de textes bruts.
2. **Enrichissement du Corpus** : Utiliser nos scripts Python (ex: `enrich_corpus.py`, `reinforce_cedilla.py`, `reinforce_weak_chars.py`) pour multiplier par 3 les caractères spéciaux et par 5 les caractères très rares.
3. **Génération GT** : Un script choisit aléatoirement une police Amazigh (dans `/training/data/fonts`), dessine l'image de la phrase sur un fond blanc, et enregistre les deux briques (`.tif` et `.gt.txt`). 
   *Note : Le modèle v3 s'est basé sur un corpus enrichi de 18 055 lignes, générant 13 711 paires d'entraînement (le fichier corrompu `tmz_latn_9586` ayant été exclu).*

### Méthode 2 : Découpage de documents existants
Si vous possédez de vrais documents scannés, vous devrez utiliser des outils comme `jTessBoxEditor` ou des scripts pour recadrer manuellement et transcrire chaque ligne.

## Déroulé de l'Entraînement 

> [!WARNING]
> **Modèle de Base (FLOAT vs INT)** : Tesseract utilise un modèle pré-existant pour démarrer (le Français `fra`). **Il est critique de télécharger la version "float"** (le meilleur modèle) depuis [tessdata_best](https://github.com/tesseract-ocr/tessdata_best). La version installée via le gestionnaire de paquets (`apt-get install tesseract-ocr-fra`) est une version "entière" (fast) **incompatible avec le fine-tuning**. Si vous utilisez la version de `apt`, l'entraînement échouera silencieusement ou affichera des erreurs de dimensions.

> [!TIP]
> **Optimisation WSL (Système de Fichiers)** : Les opérations de lecture/écriture I/O sont le goulot d'étranglement de l'entraînement. Il ne faut **jamais** entraîner sur `/mnt/c/`.
> Transférez plutôt votre dossier `tesstrain` et vos données GT dans le système de fichiers natif de WSL (ex: `/home/hamoh/tmz_training/tesstrain/`).
> *Astuce de transfert* : Utilisez la méthode du **tar pipe** pour copier rapidement des milliers de petits fichiers depuis Windows vers Linux : `tar -cf - -C /mnt/c/.../ground-truth . | tar -xf - -C /home/.../ground-truth`.

Une fois les données dans le dossier WSL natif, placez-vous dans `/home/hamoh/tmz_training/tesstrain/`.

1. **Génération du fichier UNICHARSET** : L'outil scanne vos `gt.txt` et fait l'inventaire de *toutes* les lettres utilisées : a, b, c... ɛ, ɣ, etc.
2. **Extraction des modèles existants** : L'outil va ouvrir le modèle `fra.traineddata` (version float) pour récupérer le réseau de neurones pré-entraîné du français.
3. **Apprentissage LSTM** : Il envoie vos images à la boucle, vérifie ce que le modèle devine, le compare à la vérité terrain, puis corrige les poids du réseau (Les "Iterations").

   *Commande utilisée pour le modèle v3 :*
   ```bash
   make training MODEL_NAME=tmz_latn START_MODEL=fra TESSDATA=/home/hamoh/tmz_training/tesstrain/data/tessdata_best MAX_ITERATIONS=20000
   ```

4. **Combinaison** : L'outil referme le réseau neuronal avec le nouvel unicharset dans le fichier final `tmz_latn.traineddata`.

## Métriques et Résultats (Modèle v3)

Durant l'entraînement, des "checkpoints" réguliers sont sauvegardés. L'outil évalue la qualité du modèle en utilisant deux indicateurs principaux :
- **BCER** (Best Character Error Rate) : Pourcentage de lettres incorrectes.
- **BWER** (Best Word Error Rate) : Pourcentage de mots incorrects.

**Performances atteintes (v3) :**
- Total des itérations : 20 000
- Meilleur checkpoint trouvé à l'itération : 11 517
- **BCER : 1.137%**
- **BWER : 3.420%**

Ces résultats démontrent que le modèle est très performant et prêt pour un usage en production.
