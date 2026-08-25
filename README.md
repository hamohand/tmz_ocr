# Dawaliw-ⵣ-OCR

Convertir vos documents amazighs en texte numérique.

Modèle OCR pour le **Tamazight en écriture latine**, basé sur Tesseract 5.5.0. Reconnaît les 24 caractères spéciaux amazighs : ɣ ḥ ɛ ḍ ẓ ṭ ṣ ṛ č ǧ ţ ʷ (+ majuscules et ᵒ).

## 🚀 Performances du modèle (v6)

| Métrique | v1 | v3 | v4 | v6 |
|----------|----|----|----|----|
| BCER (taux d'erreur caractère) | 2.687% | 1.137% | 0.989% | **1.505%** |
| BWER (taux d'erreur mot) | 7.488% | 3.420% | 3.000% | — |
| Paires GT d'entraînement | 4 913 | 13 711 | 22 523 | **1 187 réelles** |

> **v6** est entraîné sur des **scans réels** (pages du dictionnaire Dallet ancien et récent), contrairement aux versions précédentes qui utilisaient du texte généré synthétiquement. Sur les documents récents en 1 colonne, la précision des caractères amazighs atteint **95-100%**.

## 📖 Interface utilisateur — Dawaliw-ⵣ-OCR

Une interface simple pour les linguistes et les utilisateurs non-informaticiens :

- **Glissez** un PDF ou une image
- **Cliquez** sur « Convertir en texte ⵣ »
- **Copiez** ou **téléchargez** le résultat

### Indicateurs de qualité

| Indicateur | Source | Description |
|---|---|---|
| **Qualité caractères latins** | Tesseract | Fiabilité de la reconnaissance a, b, c... |
| **Qualité caractères amazighs ⵣ** | OCR ⇄ PDF ou OCR 150 ⇄ 300 | Fiabilité de ɣ, ḥ, ɛ, ḍ... |
| **Caractères reconnus** | OCR | Liste des lettres amazighes trouvées |

- **OCR ⇄ PDF** : comparaison avec le texte intégré du PDF (mesure exacte)
- **OCR 150 ⇄ 300** : similarité de Bray-Curtis entre 2 résolutions (estimation)

### Routes

| URL | Page |
|---|---|
| `/` | Interface simple (Dawaliw-ⵣ-OCR) |
| `/aide` | Guide d'installation et d'utilisation |
| `/expert` | Interface complète avec toutes les options |

## 🛠 Installation rapide

```bash
# 1. Télécharger et décompresser le projet
# 2. Installer Python 3.10+ (python.org) — cocher "Add to PATH"
# 3. Installer Tesseract OCR (github.com/UB-Mannheim/tesseract/wiki)
# 4. Installer les dépendances Python :
pip install fastapi uvicorn pillow python-multipart pymupdf
```

## ▶️ Lancement

```bash
cd tmz_ocr
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000
```

Ouvrir **http://localhost:8000** dans un navigateur.

## 📂 Structure du projet

```
tmz_ocr/
├── api/
│   ├── app.py                 # API FastAPI + OCR engine
│   └── static/
│       ├── simple.html        # Interface Dawaliw-ⵣ-OCR (utilisateur)
│       ├── aide.html          # Page d'aide
│       └── index.html         # Interface expert
├── models/
│   ├── tmz_latn.traineddata   # Modèle v6 (tamazight latin)
│   ├── kab.traineddata        # Modèle kab (Bouaziz Ait Driss)
│   └── fra.traineddata        # Modèle français (pour le mode hybride)
├── training/scripts/          # Scripts d'entraînement
├── docs/                      # Documentation technique
└── README.md
```

## 🔧 Architecture OCR

### Mode hybride intelligent (par défaut)

1. **tmz_latn** analyse le document en premier
2. Les mots contenant des caractères amazighs sont **verrouillés** 🔒
3. **fra** analyse le même document
4. Les mots sans caractères amazighs sont remplacés par fra si sa confiance est plus élevée

Cela garantit que les caractères spéciaux ɣ ḥ ɛ ḍ ẓ ṭ ne sont jamais remplacés par des équivalents latins (d, t, s, z...).

### DPI auto (PDF)

Le mode auto essaie 150 et 300 DPI, puis garde le résultat avec la meilleure précision sur les caractères amazighs. La similarité de Bray-Curtis compare les vecteurs de comptage par caractère.

### Normalisation Unicode

- ε (grec U+03B5) → ɛ (latin U+025B)
- Majuscules → minuscules pour les caractères spéciaux (Ẓ→ẓ, Ḍ→ḍ, etc.)

## 📊 Corpus et données

- **Corpus v6** : 1 187 paires GT réelles (scans Dallet ancien + récent)
- **Corpus v4** : 22 524 lignes synthétiques avec renforcement des caractères spéciaux
- **Wordlist** : 78 203 mots uniques (source: HuggingFace Sifal/Kabyle-French)
- **24 caractères spéciaux** : 11 paires min/maj (č/Č ḍ/Ḍ ǧ/Ǧ ḥ/Ḥ ɣ/Ɣ ṛ/Ṛ ṣ/Ṣ ṭ/Ṭ ẓ/Ẓ ɛ/Ɛ ţ/Ţ) + ʷ (U+02B7) + ᵒ (U+1D52)

> **Note** : ɛ = Latin Small Letter Open E (U+025B), à ne pas confondre avec le epsilon grec (ε, U+03B5).

## 📜 Licence

Projet de recherche pour la digitalisation de l'écriture amazighe en caractères latins.