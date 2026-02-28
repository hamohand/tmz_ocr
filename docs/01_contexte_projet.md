# Contexte et Objectifs du Projet Tamazight OCR (`tmz_ocr`)

Ce document résume nos discussions et les décisions techniques qui ont mené à la création de ce projet indépendant.

## 1. Le Besoin Initial

L'objectif de départ était d'ajouter le support de la langue **Amazigh/Berbère** à l'API OCR existante (`easytess_ocr_api`). Les documents à traiter sont écrits en **caractères latins** (Tamazight Latin : `tmz_latn`), qui incluent des lettres standards (a-z) et des caractères modifiés spécifiques (ḍ, ḥ, ɛ, ɣ, etc.).

## 2. État des lieux de Tesseract-OCR

Après recherche dans les dépôts officiels de Tesseract (version 4/5) :
- Il n'existe **aucun modèle pré-entraîné officiel** pour l'Amazigh, que ce soit en alphabet Tifinagh (`tzm`, `zgh`) ou en alphabet Latin (`ber_latn`).
- L'utilisation des modèles existants (comme le Français `fra` ou l'Anglais `eng`) permet de reconnaître les caractères latins de base, mais le moteur OCR force souvent la correction orthographique vers des mots français ou anglais, et ne reconnaît pas les caractères modifiés amazighs.

## 3. La Décision Technique : Le "Fine-Tuning"

Pour obtenir une précision professionnelle sur les textes amazighs, la décision a été prise de **créer notre propre modèle** (`tmz_latn.traineddata`).

La méthode choisie est le **fine-tuning** (ou apprentissage par transfert) : on prend un modèle robuste existant (ex: `fra.traineddata` ou `eng.traineddata`) et on poursuit son entraînement informatique en lui fournissant des milliers d'exemples de lignes de texte en Tamazight latin avec les bonnes polices de caractères.

L'outil standard de la communauté pour réaliser cette opération s'appelle `tesstrain`.

## 4. Pourquoi un projet indépendant (`tmz_ocr`) ?

Entraîner un modèle OCR est une tâche complexe qui nécessite un environnement très différent de celui d'une simple API (fichiers d'images par milliers, scripts Python/Bash, Makefile, compilation Tesseract, etc.).

Mélanger ces scripts d'entraînement dans le projet `easytess_ocr_api` aurait alourdi et complexifié le code de production.

Nous avons donc créé `C:\Users\hamoh\Documents\travail\tmz\tmz_ocr` avec une double vocation :
1. **L'atelier d'entraînement (`/training`)** : Un espace isolé où ingérer des données, lancer `tesstrain` et générer le fichier `.traineddata`.
2. **L'API de test (`/api`)** : Une petite interface FastAPI minimaliste pour vérifier la qualité du modèle généré sans avoir à le déployer tout de suite dans le gros projet `frida-micros`.

## 5. Prochaines Étapes (Roadmap)

1. Rassembler un corpus de textes en Tamazight Latin.
2. Rassembler les polices (`.ttf`) utilisées pour ces textes.
3. Générer le "Ground Truth" (Images + Fichiers textes correspondants) dans `/training/data/tmz_latn-ground-truth/`.
4. Lancer l'entraînement `make training ...` via tesstrain.
5. Déplacer le modèle produit dans `/models/tmz_latn.traineddata`.
6. Valider la reconnaissance via l'API locale (`/api`).
7. **Objectif Final** : Une fois le fichier validé, on l'intégrera définitivement dans l'API principale (`easytess_ocr_api`).
