# Prochaines Étapes et Guide de Reprise

Ce document sert de point de reprise pour continuer le travail sur le projet Tamazight OCR.

## 📅 Historique des sessions

### Session 1 (28 Février 2026)
- ✅ Création de la structure complète du projet dans `C:\Users\hamoh\Documents\travail\tmz\tmz_ocr`
- ✅ Clonage de `tesstrain` (outil officiel d'entraînement Tesseract)
- ✅ Création de l'API FastAPI (`api/app.py`)
- ✅ Création du Dockerfile
- ✅ Rédaction des documents `docs/01_contexte_projet.md` et `docs/02_workflow_entrainement.md`
- ✅ Création du script `generate_gt.py`
- ⏸️ Pause — en attente de polices et de corpus

### Session 2 (17 Juillet 2026)
- ✅ Téléchargement de 3 polices Google Noto Sans + 8 polices système — **11 polices**
- ✅ Création du script `download_corpus.py` (téléchargement depuis Hugging Face)
- ✅ Téléchargement de **4 913 phrases réelles** en Kabyle (dataset Sifal/Kabyle-French, Tatoeba)
- ✅ Génération de **4 913 paires Ground Truth** (images `.tif` + texte `.gt.txt`)
- ✅ Installation de Tesseract 5.5.0 + outils d'entraînement dans WSL-Ubuntu
- ✅ **Entraînement complet** — 10 000 itérations LSTM, fine-tuning depuis `fra` (best)
- ✅ **Modèle `tmz_latn.traineddata` (v1) créé** — BCER = 2.687%, 3.1 Mo
- ✅ Tests de validation : 7/13 exact match, erreurs mineures sur les autres
- ✅ Intégration du modèle dans `easytess_ocr_api`
- ✅ Mise à jour de toute la documentation

### Session 3 (7-8 Août 2026)
- ✅ Création d'un corpus enrichi avec `enrich_corpus.py` (multiplication des caractères spéciaux et rares)
- ✅ 18 055 lignes générées, rendues en 13 711 paires GT (fichier corrompu `tmz_latn_9586` exclu)
- ✅ Migration de l'entraînement vers le système de fichiers natif WSL (`/home/hamoh/tmz_training/`) pour améliorer les performances E/S
- ✅ **Entraînement v3 complet** — 20 000 itérations (meilleur checkpoint à 11 517), 13 711 images
- ✅ **Performances exceptionnelles** : BCER = 1.137%, BWER = 3.420%
- ✅ Améliorations de l'API : mode hybride OCR (`fra+tmz_latn`), détection Auto-PSM, analyse de précision des signes diacritiques par caractère
- ✅ Interface web en Dark mode avec glisser-déposer

---

## ✅ Projet terminé — Modèle v3 opérationnel

Le modèle `tmz_latn.traineddata` (v3) est **entraîné et hautement performant**.

### Performances (Comparaison v1 vs v3)

| Métrique | v1 (Session 2) | v3 (Session 3) |
|----------|----------------|----------------|
| BCER (erreur caractères) | 2.687% | **1.137%** |
| BWER (erreur mots) | 7.488% | **3.420%** |
| Taille du modèle | 3.1 Mo | 3.1 Mo |
| Corpus d'entraînement | 4 913 images | 13 711 images |
| Itérations | 10 000 | 20 000 (best à 11 517) |
| Modèle de base | `fra` (tessdata_best) | `fra` (float version from tessdata_best) |

### Emplacements du modèle et de l'entraînement

| Composant | Chemin |
|-------------|--------|
| Projet tmz_ocr | `models/tmz_latn.traineddata` |
| API easytess | Intégré dans le Dockerfile |
| Entraînement natif WSL | `/home/hamoh/tmz_training/` (Performances E/S ext4) |

---

## 🔧 Améliorations possibles (optionnel)

### 1. Augmenter davantage le corpus
- Modifier `MAX_LINES=20000` dans `download_corpus.py` (Le dataset complet contient **115 269 phrases**)
- Poursuivre l'enrichissement manuel des cas rares.

### 2. Pousser l'entraînement
- Tester avec plus de 20 000 itérations ou ajuster le learning rate.
- Le meilleur checkpoint actuel est à 11 517 itérations.

### 3. Ajouter des polices
- Polices SIL (Doulos, Charis, Andika) pour une meilleure diversité
- La police "Tamazight Latin" de happy05dz

### 4. Ajouter du bruit aux images
- Modifier `generate_gt.py` pour ajouter du bruit, rotation, flou
- Rend le modèle plus robuste face à des scans réels

---

## 🔑 Fichiers clés

| Fichier | Rôle |
|---------|------|
| `models/tmz_latn.traineddata` | **Le modèle final v3** |
| `training/scripts/download_corpus.py` | Télécharge les phrases depuis Hugging Face |
| `training/scripts/enrich_corpus.py` | Enrichit le corpus en multipliant les caractères spéciaux (x3) et rares (x5) |
| `training/scripts/reinforce_cedilla.py` | Script de renforcement (Session 3) |
| `training/scripts/reinforce_weak_chars.py` | Script de renforcement (Session 3) |
| `training/scripts/generate_gt.py` | Génère les images d'entraînement |
| `training/scripts/run_training.sh` | Lance l'entraînement (adapté pour WSL `/home/hamoh/tmz_training/`) |
| `training/scripts/lignes_tamazight_enrichi.txt` | Corpus enrichi de 18 055 lignes |
| `docs/03_ressources_donnees.md` | Inventaire des ressources |
