# Ressources et Données

Ce document détaille les ressources utilisées pour l'entraînement du modèle OCR Tamazight.

## 📝 Corpus Textuel

### Corpus Original
- **Source** : Sifal/Kabyle-French, issu de Tatoeba (via Hugging Face).
- **Taille** : 4 913 phrases réelles en Kabyle.

### Corpus Enrichi (v3)
- **Source** : Généré à partir du corpus original.
- **Taille** : 18 055 lignes (`lignes_tamazight_enrichi.txt`).
- **Scripts utilisés** :
  - `enrich_corpus.py` : Multiplie les phrases contenant des caractères spéciaux (x3) et des caractères rares (x5) pour forcer le modèle à mieux les apprendre.
  - `reinforce_cedilla.py` et `reinforce_weak_chars.py` : Scripts de renforcement spécifiques pour les caractères difficiles.
- **Fichiers additionnels** : `lignes_tamazight_renforce.txt`, `lignes_tamazight_v3.txt`.

## 🖼 Ground Truth (Images + Texte)

- **Volume total** : 13 711 paires générées (`.tif` + `.gt.txt`) à partir des 18 055 lignes enrichies (augmentation depuis les 4 913 initiales).
- *Note : Le fichier corrompu `tmz_latn_9586` a été exclu de l'entraînement v3.*

## 🔤 Polices (Fonts)

11 polices au total ont été utilisées pour la génération du Ground Truth, garantissant une bonne diversité typographique pour le modèle :
- 3 polices Google Noto Sans.
- 8 polices système standard.

## 🔠 Alphabet et Caractères Spéciaux

Le modèle prend en charge l'alphabet latin enrichi utilisé pour le Tamazight. Une attention particulière a été portée sur les 20 caractères spéciaux suivants (minuscules et majuscules) :
**č, ḍ, ǧ, ḥ, ɣ, ṛ, ṣ, ṭ, ẓ, ɛ**

## 🤖 Modèle de Base
- L'entraînement a été réalisé en fine-tuning à partir du modèle français `fra.traineddata`.
- **Important** : La version utilisée est la version *float* provenant de `tessdata_best`, et non la version integer du dépôt apt.
