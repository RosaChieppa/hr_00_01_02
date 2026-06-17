import os

class ImpostazioniSistema:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CARTELLA_CURRICULA = os.path.join(BASE_DIR, "resumes")
    PERCORSO_PERSISTENZA_DB = os.path.join(BASE_DIR, "data", "chromadb_locale")
    NOME_COLLEZIONE = "archivio_cv_vettoriale_locale"
    
    MODELLO_VETTORIALE = "nomic-embed-text"  # Questo verrà gestito da Ollama
    MODELLO_CHAT = "llama3"
    URL_ENDPOINT_API = "http://127.0.0.1:11434"
