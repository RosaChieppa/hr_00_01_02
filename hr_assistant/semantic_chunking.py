import os
import re
import numpy as np
from config import ImpostazioniSistema
from custom_embeddings import CustomLocalEmbeddings

class SemanticChunking:
    def __init__(self, model_folder=None, model_name=None):
        """Inizializza lo chunking usando Ollama come motore di calcolo vettoriale."""
        print(f"Inizializzazione dello Chunking Semantico tramite Ollama: {ImpostazioniSistema.MODELLO_VETTORIALE}")
        self.embeddings_model = CustomLocalEmbeddings()

    def _cosine_similarity_numpy(self, a, b):
        """Calcola la similarità coseno usando NumPy."""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    def calculate_cosine_distances(self, sentences):
        distances = []
        for i in range(len(sentences) - 1):
            embedding_current = np.array(sentences[i]["combined_sentence_embedding"])
            embedding_next = np.array(sentences[i + 1]["combined_sentence_embedding"])

            similarity = self._cosine_similarity_numpy(embedding_current, embedding_next)
            distance = 1.0 - similarity
            distances.append(distance)
            sentences[i]["distance_to_next"] = distance
        return distances, sentences

    def combine_sentences(self, sentences, buffer_size=1):
        for i in range(len(sentences)):
            combined_sentence = ""
            for j in range(i - buffer_size, i):
                if j >= 0:
                    combined_sentence += sentences[j]["sentence"] + " "
            combined_sentence += sentences[i]["sentence"] + " "
            for j in range(i + 1, i + 1 + buffer_size):
                if j < len(sentences):
                    combined_sentence += sentences[j]["sentence"] + " "
            sentences[i]["combined_sentence"] = combined_sentence.strip()
        return sentences

    def create_chunks(self, text, buffer_size=1, percentile_threshold=95):
        """Funzione principale per eseguire lo chunking semantico sul testo."""
        if not text.strip():
            return []

        single_sentences = re.split(r'(?<=[.?!])\s+', text.strip())
        sentences = [{"sentence": x, "index": i} for i, x in enumerate(single_sentences) if x.strip()]
        
        if not sentences:
            return [text]

        sentences = self.combine_sentences(sentences, buffer_size=buffer_size)
        combined_text_list = [s["combined_sentence"] for s in sentences]
        
        embeddings = self.embeddings_model.embed_documents(combined_text_list)
        
        for i, emb in enumerate(embeddings):
            sentences[i]["combined_sentence_embedding"] = emb
            
        distances, sentences = self.calculate_cosine_distances(sentences)
        if not distances:
            return [text]
            
        breakpoint_threshold = np.percentile(distances, percentile_threshold)
        chunks = []
        current_chunk = ""
        
        for i in range(len(sentences)):
            current_chunk += sentences[i]["sentence"] + " "
            if i < len(sentences) - 1 and sentences[i]["distance_to_next"] > breakpoint_threshold:
                chunks.append(current_chunk.strip())
                current_chunk = ""
                
        if current_chunk:
            chunks.append(current_chunk.strip())
        return chunks
