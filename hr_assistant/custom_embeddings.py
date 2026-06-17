import httpx
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from config import ImpostazioniSistema

class CustomLocalEmbeddings:
    def __init__(self, model_folder=None):
        # Utilizziamo l'endpoint di Ollama per generare i vettori in locale
        self.api_url = f"{ImpostazioniSistema.URL_ENDPOINT_API}/api/embeddings"
        self.model_name = ImpostazioniSistema.MODELLO_VETTORIALE

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Genera gli embedding chiamando direttamente le API locali di Ollama."""
        embeddings = []
        with httpx.Client(timeout=60.0) as client:
            for text in texts:
                if not text.strip():
                    continue
                try:
                    response = client.post(
                        self.api_url,
                        json={"model": self.model_name, "prompt": text}
                    )
                    if response.status_code == 200:
                        embeddings.append(response.json()["embedding"])
                    else:
                        # Fallback su vettore neutro in caso di anomalia
                        embeddings.append([0.0] * 768)
                except Exception:
                    embeddings.append([0.0] * 768)
        return embeddings

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.generate_embeddings(texts)

    def embed_query(self, text: str) -> list[float]:
        res = self.generate_embeddings([text])
        return res[0] if res else [0.0] * 768


class CustomEmbeddingFunction(EmbeddingFunction):
    """Wrapper compatibile al 100% con le specifiche di ChromaDB."""
    def __init__(self):
        self.engine_locale = CustomLocalEmbeddings()

    def __call__(self, input: Documents) -> Embeddings:
        if not input:
            return []
        return self.engine_locale.generate_embeddings(list(input))
