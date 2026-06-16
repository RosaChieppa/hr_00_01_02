import os

class ImpostazioniSistema:
    # Trova la cartella principale (MIO-PROGETTO-HR) salendo di un livello da hr_assistant
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Percorsi assoluti allineati alla struttura del tuo progetto
    CARTELLA_CURRICULA = os.path.join(BASE_DIR, "resumes")
    PERCORSO_PERSISTENZA_DB = os.path.join(BASE_DIR, "data", "chromadb_locale")
    
    # Configurazione ChromaDB
    NOME_COLLEZIONE = "archivio_cv_vettoriale_locale"
    
    # Configurazione Modelli Ollama (Locali)
    MODELLO_VETTORIALE = "nomic-embed-text"
    MODELLO_CHAT = "llama3"
    URL_ENDPOINT_API = "http://127.0.0.1:11434"
