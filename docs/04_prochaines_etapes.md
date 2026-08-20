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

### Session 4 (9-10 Août 2026)
- ✅ Augmentation de données (9 transformations dans `generate_gt.py`)
- ✅ Création du dictionnaire de mots de 78 203 mots (`build_wordlist_hf.py`)
- ✅ Renforcement des majuscules (`reinforce_uppercase.py`, 500 occurrences par lettre majuscule)
- ✅ Entraînement 2nd pass (tmz_latn v3 → v4) sur un corpus de 22 524 lignes (22 523 images)
- ✅ Tests réels : 87.6% de confiance moyenne sur 6 pages scannées de M. Bouaziz
- ✅ Intégration et comparaison avec le modèle `kab` (Bouaziz Ait Driss)
- ✅ Mise à jour de l'API vers v4.0.0 (correction du health check)
### Session 5 (11-20 Août 2026)
- ✅ Création du pipeline PDF vers GT (`pdf_to_gt.py` avec `--split-columns`)
- ✅ Extraction de 658 lignes depuis 5 documents réels scannés (Dictionnaire Dallet, Smail Abdenbi, Tasɣunt Aselmad, etc.), 548 conservées après filtrage du français (`filter_french_gt.py`)
- ✅ Ajout des consonnes labio-vélarisées ʷ/ᵒ
- ✅ Gestion de la régression v5a (pollution par GT français) et amélioration v5b après filtrage
- ✅ Palette de caractères ajoutée dans `review.html`
- ✅ **Entraînement v5 complet (v5b)** — BCER = 1.271% (meilleur checkpoint à 19 100/20 000)
- ✅ **Performances sur scans réels** : 86.5% de confiance moyenne (bat le modèle kab sur 4/6 pages), meilleur résultat à 90.2% (ATagrest_urghu_5)
- ✅ Enrichissement spécifique des labio-vélarisées (`enrich_labiovelar.py`) et application de corrections (`apply_corrections.py`)

---

## ✅ Projet terminé — Modèle v5 opérationnel

Le modèle `tmz_latn.traineddata` (v5) est **entraîné et hautement performant**.

### Performances (Comparaison v3, v4, v5)

| Métrique | v3 (Session 3) | v4 (Session 4) | v5 (Session 5) |
|----------|----------------|----------------|----------------|
| BCER (erreur caractères) | 1.137% | **0.989%** | 1.271% |
| BWER (erreur mots) | 3.420% | **3.000%** | N/A |
| Taille du modèle | 3.1 Mo | 4.0 Mo | **4.19 Mo** |
| Corpus d'entraînement | 13 711 images | 22 523 images | **23 607 images** (23 059 synth + 548 réelles) |
| Itérations | 20 000 (best à 11 517) | 19 000 (best à 5 420) | **20 000** (best à 19 100) |
| Modèle de base | `fra` (float version) | `tmz_latn` v3 | **`tmz_latn` v4** (3rd pass) |
| Confiance sur scans réels | N/A | 87.6% | **86.5%** (avec labio-vélarisées, 90.2% max) |

### Emplacements du modèle et de l'entraînement

| Composant | Chemin |
|-------------|--------|
| Projet tmz_ocr | `models/tmz_latn.traineddata` |
| API easytess | Intégré dans le Dockerfile |
| Entraînement natif WSL | `/home/hamoh/tmz_training/` (Performances E/S ext4) |

---

## 🔧 Améliorations possibles (optionnel)

### 1. Augmenter davantage le corpus (Fait ✅)
- Modifier `MAX_LINES=20000` dans `download_corpus.py` (Le dataset complet contient **115 269 phrases**)
- Poursuivre l'enrichissement manuel des cas rares. (Corpus v4 : 22 524 lignes)

### 2. Pousser l'entraînement
- Tester avec plus de 20 000 itérations ou ajuster le learning rate.
- Le meilleur checkpoint actuel (v4) est à 5 420 itérations.

### 3. Ajouter des polices
- Polices SIL (Doulos, Charis, Andika) pour une meilleure diversité
- La police "Tamazight Latin" de happy05dz

### 4. Ajouter du bruit aux images (Fait ✅)
- Modifier `generate_gt.py` pour ajouter du bruit, rotation, flou (9 transformations implémentées)
- Rend le modèle plus robuste face à des scans réels (Testé: 87.6% sur les scans)

---

## 🔑 Fichiers clés

| Fichier | Rôle |
|---------|------|
| `models/tmz_latn.traineddata` | **Le modèle final v5** |
| `training/scripts/download_corpus.py` | Télécharge les phrases depuis Hugging Face |
| `training/scripts/enrich_corpus.py` | Enrichit le corpus en multipliant les caractères spéciaux (x3) et rares (x5) |
| `training/scripts/enrich_labiovelar.py` | Enrichit spécifiquement les occurrences des consonnes labio-vélarisées (ʷ/ᵒ) |
| `training/scripts/apply_corrections.py` | Applique des corrections ciblées sur le texte |
| `training/scripts/pdf_to_gt.py` | Extrait les lignes depuis des PDF pour la création de vérité terrain réelle |
| `training/scripts/filter_french_gt.py` | Filtre les lignes pur français de la vérité terrain réelle |
| `training/scripts/prepare_v5.sh` | Script de préparation des données pour v5 |
| `training/scripts/train_v5b.sh` | Script d'entraînement pour v5b |
| `training/scripts/reinforce_cedilla.py` | Script de renforcement (Session 3) |
| `training/scripts/reinforce_weak_chars.py` | Script de renforcement (Session 3) |
| `training/scripts/reinforce_uppercase.py` | Renforcement des majuscules à hauteur de 500 occurrences (Session 4) |
| `training/scripts/build_wordlist_hf.py` | Construit le dictionnaire de 78 203 mots |
| `training/scripts/create_lang_files.sh` | Crée les fichiers punc et numbers pour `combine_lang_model` |
| `training/scripts/test_compare.py` | Teste et compare le modèle avec le modèle `kab` |
| `training/scripts/generate_gt.py` | Génère les images d'entraînement (avec 9 transformations) |
| `training/scripts/run_training.sh` | Lance l'entraînement (adapté pour WSL `/home/hamoh/tmz_training/`) |
| `training/scripts/lignes_tamazight_enrichi.txt` | Corpus enrichi de 22 524 lignes |
| `docs/03_ressources_donnees.md` | Inventaire des ressources |
