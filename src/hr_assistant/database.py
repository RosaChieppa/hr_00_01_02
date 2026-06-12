# database.py
import chromadb
from chromadb.utils import embedding_functions
from hr_assistant.config import ImpostazioniSistema


class GestoreDatabaseVettoriale:
    def __init__(self):
        # Configurazione della funzione di embedding proprietaria di OpenAI
        self.funzione_embedding_openai = embedding_functions.OpenAIEmbeddingFunction(
            api_key=ImpostazioniSistema.CHIAVE_OPENAI_EMBEDDING, 
            model_name=ImpostazioniSistema.MODELLO_VETTORIALE
        )

        # Inizializzazione del client persistente per salvare i vettori su disco
        self.client_locale = chromadb.PersistentClient(path=ImpostazioniSistema.PERCORSO_PERSISTENZA_DB)
        self.collezione_dati = self.client_locale.get_or_create_collection(
            name=ImpostazioniSistema.NOME_COLLEZIONE, 
            embedding_function=self.funzione_embedding_openai
        )

    def inserisci_documentazione(self, testi_cv, metadati_file, codici_id):
        """Aggiunge i segmenti dei curricula estratti nella collezione vettoriale."""
        self.collezione_dati.add(documents=testi_cv, metadatas=metadati_file, ids=codici_id)

    def effettua_ricerca_semantica(self, testo_ricerca, numero_risultati=1):
        """Interroga la collezione per similarità semantica rispetto alla query utente."""
        return self.collezione_dati.query(query_texts=[testo_ricerca], n_results=numero_risultati)
