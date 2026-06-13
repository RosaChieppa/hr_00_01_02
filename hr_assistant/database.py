# database.py
import chromadb
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from ollama import Client
from hr_assistant.config import ImpostazioniSistema

# Creiamo una funzione di embedding personalizzata usando il client ufficiale Ollama
class FunzioneEmbeddingOllamaPersonalizzata(EmbeddingFunction):
    def __init__(self):
        self.client_ollama = Client(host=ImpostazioniSistema.URL_ENDPOINT_API)
        self.modello = ImpostazioniSistema.MODELLO_VETTORIALE

    def __call__(self, input: Documents) -> Embeddings:
        lista_vettori = []
        for testo in input:
            risposta = self.client_ollama.embeddings(model=self.modello, prompt=testo)
            lista_vettori.append(risposta["embedding"])
        return lista_vettori


class GestoreDatabaseVettoriale:
    def __init__(self):
        # Usiamo la nostra funzione personalizzata infallibile
        self.funzione_embedding = FunzioneEmbeddingOllamaPersonalizzata()

        # Inizializzazione del client persistente su disco
        self.client_locale = chromadb.PersistentClient(path=ImpostazioniSistema.PERCORSO_PERSISTENZA_DB)
        self.collezione_dati = self.client_locale.get_or_create_collection(
            name=ImpostazioniSistema.NOME_COLLEZIONE, 
            embedding_function=self.funzione_embedding
        )

    def inserisci_documentazione(self, testi_cv, metadati_file, codici_id):
        """Aggiunge i segmenti dei curricula estratti nella collezione vettoriale."""
        if self.collezione_dati.count() == 0:
            print("💾 Popolamento del database vettoriale locale in corso...")
            self.collezione_dati.add(documents=testi_cv, metadatas=metadati_file, ids=codici_id)
            print(f"✅ Inseriti correttamente {self.collezione_dati.count()} elementi!")
        else:
            print(f"📦 Il database contiene già {self.collezione_dati.count()} elementi. Salto l'inserimento.")

    def effettua_ricerca_semantica(self, testo_ricerca, numero_risultati=1):
        """Interroga la collezione per similarità semantica rispetto alla query utente."""
        # CORREZIONE APPLICATA: Sostituito numero_results con numero_risultati
        return self.collezione_dati.query(query_texts=[testo_ricerca], n_results=numero_risultati)
