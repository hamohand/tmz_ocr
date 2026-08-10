"""
Script pour télécharger le dataset Sifal/Kabyle-French depuis Hugging Face
et extraire les phrases en Kabyle (Latin) pour l'entraînement OCR.
"""
import urllib.request
import json
import os

OUTPUT_FILE = "lignes_tamazight.txt"
DATASET = "Sifal/Kabyle-French"
CONFIG = "default"
SPLIT = "train"
BATCH_SIZE = 100  # L'API retourne 100 lignes max par requête
MAX_LINES = 5000  # On limite à 5000 pour un premier entraînement

# Le nom de la colonne Kabyle (c'est le header du CSV original)
KAB_COL = "Ẓriɣ dacu ara d-tiniḍ."

def fetch_rows(offset, length):
    """Récupère un lot de lignes depuis l'API Hugging Face"""
    url = (
        f"https://datasets-server.huggingface.co/rows"
        f"?dataset={DATASET}&config={CONFIG}&split={SPLIT}"
        f"&offset={offset}&length={length}"
    )
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def clean_line(text):
    """Nettoie une ligne de texte"""
    text = text.strip()
    # Supprimer les lignes vides ou trop courtes
    if len(text) < 3:
        return None
    # Supprimer les lignes qui ne sont que des chiffres ou ponctuations
    if all(c.isdigit() or c in ".,;:!?-() " for c in text):
        return None
    return text

def main():
    print(f"=== Téléchargement du corpus Kabyle depuis Hugging Face ===")
    print(f"Dataset: {DATASET}")
    print(f"Objectif: {MAX_LINES} phrases")
    print()
    
    all_lines = []
    offset = 0
    
    while len(all_lines) < MAX_LINES:
        remaining = MAX_LINES - len(all_lines)
        batch = min(BATCH_SIZE, remaining)
        
        try:
            data = fetch_rows(offset, batch)
            rows = data.get("rows", [])
            
            if not rows:
                print(f"Plus de données à l'offset {offset}")
                break
            
            for row in rows:
                kab_text = row["row"].get(KAB_COL, "")
                cleaned = clean_line(kab_text)
                if cleaned:
                    all_lines.append(cleaned)
            
            print(f"  Téléchargé: {offset + len(rows)} lignes, "
                  f"retenu: {len(all_lines)} phrases valides")
            
            offset += len(rows)
            
        except Exception as e:
            print(f"Erreur à l'offset {offset}: {e}")
            break
    
    # Dédupliquer
    unique_lines = list(dict.fromkeys(all_lines))
    print(f"\nAprès déduplication: {len(unique_lines)} phrases uniques")
    
    # Sauvegarder
    output_path = os.path.join(os.path.dirname(__file__), OUTPUT_FILE)
    with open(output_path, "w", encoding="utf-8") as f:
        for line in unique_lines:
            f.write(line + "\n")
    
    print(f"Sauvegardé dans: {output_path}")
    print(f"Total: {len(unique_lines)} phrases")

if __name__ == "__main__":
    main()
