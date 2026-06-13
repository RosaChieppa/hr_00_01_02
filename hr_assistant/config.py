# config.py
import os

class ImpostazioniSistema:
    # Trova la cartella principale (MIO-PROGETTO-HR) salendo di un livello da hr_assistant
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Percorsi assoluti corretti allineati alla struttura delle cartelle
    CARTELLA_CURRICULA = os.path.join(BASE_DIR, "resumes")
    PERCORSO_PERSISTENZA_DB = os.path.join(BASE_DIR, "data", "chromadb_locale")
    
    NOME_COLLEZIONE = "archivio_cv_vettoriale_locale"
    MODELLO_VETTORIALE = "nomic-embed-text"
    MODELLO_CHAT = "llama3"
    URL_ENDPOINT_API = "http://127.0.0.1:11434"
