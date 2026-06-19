import os

class ImpostazioniSistema:
    # Directory principale del progetto
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Cartelle per i dati fisici e il database vettoriale
    CARTELLA_CURRICULA = os.path.join(BASE_DIR, "resumes")
    PERCORSO_PERSISTENZA_DB = os.path.join(BASE_DIR, "data", "chromadb_locale")
    NOME_COLLEZIONE = "archivio_cv_vettoriale_locale"
    
    # Modelli locali gestiti da Ollama
    MODELLO_VETTORIALE = "nomic-embed-text"
    MODELLO_CHAT = "llama3"
    
    # Endpoint delle API locali di Ollama
    URL_ENDPOINT_API = "http://127.0.0.1:11434"
