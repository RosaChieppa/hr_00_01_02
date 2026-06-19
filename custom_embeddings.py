import httpx
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from config import ImpostazioniSistema

class CustomLocalEmbeddings:
    def __init__(self, model_folder=None):
        self.api_url = f"{ImpostazioniSistema.URL_ENDPOINT_API}/api/embeddings"
        self.model_name = ImpostazioniSistema.MODELLO_VETTORIALE

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Genera gli embedding chiamando l'API locale di Ollama in modo sequenziale sicuro."""
        embeddings = []
        
        with httpx.Client(timeout=60.0) as client:
            for text in texts:
                if not text or not text.strip():
                    embeddings.append([0.0] * 768)
                    continue
                try:
                    response = client.post(
                        self.api_url,
                        json={"model": self.model_name, "prompt": text.strip()}
                    )
                    if response.status_code == 200:
                        embeddings.append(response.json()["embedding"])
                    else:
                        print(f"⚠️ Errore Ollama {response.status_code}: {response.text}")
                        embeddings.append([0.0] * 768)
                except Exception as e:
                    print(f"❌ Errore di connessione durante l'embedding: {e}")
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
