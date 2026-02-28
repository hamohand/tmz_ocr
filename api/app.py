from fastapi import FastAPI, File, UploadFile, HTTPException
import pytesseract
from PIL import Image
import io
import os

app = FastAPI(title="Tamazight OCR API", description="API légère pour OCR du Tamazight Latin")

# Configuration du chemin TESSDATA pour forcer Tesseract à chercher dans notre dossier models/
# Assurez-vous d'ajuster ce chemin absolu ou d'utiliser une variable d'environnement
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))
os.environ["TESSDATA_PREFIX"] = MODELS_DIR

@app.get("/")
def read_root():
    return {"message": "Tamazight OCR API is running. Utilisez POST /ocr pour traduire une image."}

@app.post("/ocr")
async def perform_ocr(file: UploadFile = File(...)):
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Le fichier doit être une image.")
    
    try:
        content = await file.read()
        image = Image.open(io.BytesIO(content))
        
        # On force explicitement l'utilisation de tmz_latn
        text = pytesseract.image_to_string(image, lang='tmz_latn')
        
        return {
            "lang": "tmz_latn",
            "text": text.strip()
        }
    except pytesseract.TesseractError as e:
        raise HTTPException(status_code=500, detail=f"Erreur Tesseract. Avez-vous bien placé tmz_latn.traineddata dans le dossier models ? Erreur: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

# Pour lancer : uvicorn app:app --host 0.0.0.0 --port 8000
