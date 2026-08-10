import os
import string

# Définition des chemins de fichiers
DOSSIER_SCRIPTS = r"C:\Users\hamoh\Documents\travail\tmz\tmz_ocr\training\scripts"
FICHIERS_CORPUS = [
    "lignes_tamazight.txt",
    "lignes_tamazight_enrichi.txt",
    "lignes_tamazight_v3.txt",
    "lignes_tamazight_renforce.txt"
]
FICHIER_SORTIE = r"C:\Users\hamoh\Documents\travail\tmz\tmz_ocr\training\data\tmz_latn.wordlist"

# Ensemble des caractères spéciaux tamazight
CARACTERES_SPECIAUX = set("čḍǧḥɣṛṣṭẓɛČḌǦḤƔṚṢṬẒƐ")

def main():
    mots_uniques = set()
    
    # Assurer que le dossier de sortie existe
    os.makedirs(os.path.dirname(FICHIER_SORTIE), exist_ok=True)
    
    # Liste complète de ponctuation à retirer (inclut les guillemets français et typographiques)
    ponctuation_a_retirer = string.punctuation + "«»“”‘’…"
    
    for nom_fichier in FICHIERS_CORPUS:
        chemin_complet = os.path.join(DOSSIER_SCRIPTS, nom_fichier)
        if os.path.exists(chemin_complet):
            print(f"Lecture du fichier : {nom_fichier}")
            try:
                with open(chemin_complet, 'r', encoding='utf-8') as f:
                    for ligne in f:
                        # Diviser par espaces
                        mots = ligne.split()
                        for mot in mots:
                            # Retirer la ponctuation en début et fin de mot
                            mot_nettoye = mot.strip(ponctuation_a_retirer)
                            if mot_nettoye:
                                mots_uniques.add(mot_nettoye)
            except Exception as e:
                print(f"Erreur lors de la lecture de {nom_fichier}: {e}")
        else:
            print(f"Fichier non trouvé (ignoré) : {nom_fichier}")
    
    # Trier alphabétiquement en tenant compte de la casse
    liste_mots_triee = sorted(list(mots_uniques))
    
    # Identifier les mots contenant des caractères spéciaux tamazight
    mots_speciaux = [mot for mot in liste_mots_triee if any(c in CARACTERES_SPECIAUX for c in mot)]
    
    # Écriture dans le fichier de sortie
    print(f"Écriture de la wordlist dans : {FICHIER_SORTIE}")
    try:
        with open(FICHIER_SORTIE, 'w', encoding='utf-8') as f:
            for mot in liste_mots_triee:
                f.write(mot + "\n")
    except Exception as e:
        print(f"Erreur lors de l'écriture: {e}")
            
    # Affichage des statistiques
    print("\n--- Statistiques ---")
    print(f"Nombre total de mots uniques extraits : {len(liste_mots_triee)}")
    print(f"Nombre de mots avec caractères spéciaux tamazight : {len(mots_speciaux)}")

if __name__ == "__main__":
    main()
