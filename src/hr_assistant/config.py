# config.py
import os

class ImpostazioniSistema:
    # Directory e parametri strutturali del database vettoriale
    CARTELLA_CURRICULA = "resumes"
    NOME_COLLEZIONE = "archivio_cv_vettoriale"
    PERCORSO_PERSISTENZA_DB = "data/chromadb_locale"
    
    # Configurazione dei modelli di Embedding
    MODELLO_VETTORIALE = "text-embedding-3-small"
    CHIAVE_OPENAI_EMBEDDING = "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"
    
    # Configurazione del modello di completamento e Chat LLM
    MODELLO_CHAT = "gpt-4o-mini"
    URL_ENDPOINT_API = "https://openai.com"
    CHIAVE_OPENAI_CHAT = "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"
