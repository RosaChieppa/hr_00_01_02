# custom_embedding.py
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from ollama import Client
from hr_assistant.config import ImpostazioniSistema

class CustomEmbeddingFunction(EmbeddingFunction):
    """
    Funzione di embedding personalizzata usando il client ufficiale Ollama.
    Isolata in questo file per rispettare il principio di singola responsabilità.
    """
    def __init__(self):
        # Utilizza l'endpoint e il modello centralizzati nelle impostazioni di sistema
        self.client_ollama = Client(host=ImpostazioniSistema.URL_ENDPOINT_API)
        self.modello = ImpostazioniSistema.MODELLO_VETTORIALE

    def __call__(self, input: Documents) -> Embeddings:
        lista_vettori = []
        for testo in input:
            if not testo.strip():
                lista_vettori.append([])
                continue
            try:
                risposta = self.client_ollama.embeddings(model=self.modello, prompt=testo)
                lista_vettori.append(risposta["embedding"])
            except Exception as e:
                print(f"❌ Errore nella generazione del vettore con Ollama: {e}")
                raise e
        return lista_vettori
