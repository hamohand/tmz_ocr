# Tamazight OCR Project (tmz_ocr)

Modèle OCR pour la langue Tamazight (Berbère) basé sur Tesseract 5.5.0.

## 🚀 Performances du Modèle (v4)

Le modèle a été significativement amélioré lors de la Session 4 (9-10 Août 2026).

| Métrique | v1 | v3 | v4 |
|----------|----|----|----|
| BCER (Character Error Rate) | 2.687% | 1.137% | **0.989%** |
| BWER (Word Error Rate) | 7.488% | 3.420% | **3.000%** |
| Itérations d'entraînement | 10 000 | 20 000 | 19 000 (best: 5 420) |
| Taille du corpus | 4 913 paires GT | 13 711 paires GT | 22 523 paires GT |
| Taille du modèle | - | - | 4.0 MB |

*Entraînement v4 réalisé en fine-tuning 2nd pass (tmz_latn v3 → v4).*
*Test sur scans réels : 87.6% de confiance moyenne, surpasse le modèle kab (Bouaziz Ait Driss, intégré pour comparaison - CER 5.08%, WER 15.28%) sur 4 pages sur 6.*

*Entraînement v3 réalisé sur le système de fichiers natif WSL (`/home/hamoh/tmz_training/`) pour des performances E/S optimales sur ext4.*

## 📂 Corpus et Données

- **Corpus v4** : 22 524 lignes avec renforcement des caractères spéciaux majuscules (~500 occurrences chacun).
- **Wordlist** : 78 203 mots uniques intégrés (source: HuggingFace Sifal/Kabyle-French, 115K phrases).
- **Ground Truth (GT)** : 22 523 images générées avec augmentation des données (bruit Gaussien, rotation, flou, contraste, luminosité, arrière-plans texturés, tailles de polices variables).
- **Caractères spéciaux pris en charge (22)** : 11 paires min/maj (č/Č, ḍ/Ḍ, ǧ/Ǧ, ḥ/Ḥ, ɣ/Ɣ, ṛ/Ṛ, ṣ/Ṣ, ṭ/Ṭ, ẓ/Ẓ, ɛ/Ɛ, ţ/Ţ).
  > **Note** : ɛ = Latin Small Letter Open E (U+025B), à ne pas confondre avec le epsilon grec (ε, U+03B5).
- **Fichiers annexes** : `tmz_latn.punc` (19 caractères), `tmz_latn.numbers` (10 chiffres).

## 🛠 Structure du Projet

- `api/` : API OCR v4.0.0 avec 4 modes (hybride, tmz_only, kab_only, compare), détection Auto-PSM et analyse de précision.
- `models/` : Contient le modèle entraîné `tmz_latn.traineddata` (v4). Intègre aussi le modèle `kab` de Bouaziz Ait Driss pour comparaison.
- `training/scripts/` :
  - Nouveaux scripts v4 : `reinforce_uppercase.py`, `build_wordlist_hf.py`, `build_wordlist.py`, `test_compare.py`.
  - Scripts existants : `enrich_corpus.py`, `reinforce_cedilla.py`, `reinforce_weak_chars.py`, `download_corpus.py`, `generate_gt.py`.
- `docs/` : Documentation complète du projet.

## 💻 API et Interface Web

L'API v4.0.0 propose désormais des fonctionnalités avancées :
- **4 modes OCR** : hybride (`fra+tmz_latn`), `tmz_only`, `kab_only`, et `compare`.
- **Modèle de comparaison** : Intégration du modèle `kab` (Bouaziz Ait Driss).
- **Détection Auto-PSM**
- **Analyse de précision par caractère** (focus sur les signes diacritiques)
- **Interface Web Dark Mode** : UI modernisée avec support du glisser-déposer.

## 🔧 Utilisation

Voir la documentation dans le dossier `docs/` pour plus de détails sur le workflow et les ressources.