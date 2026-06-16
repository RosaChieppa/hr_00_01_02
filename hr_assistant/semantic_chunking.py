# semantic_chunking.py
import re
import numpy as np
from langchain_ollama import OllamaEmbeddings 
from sklearn.metrics.pairwise import cosine_similarity

class SemanticChunking:
    def __init__(self, model_name="nomic-embed-text"):
        """
        Inizializza gli embeddings di Ollama.
        Assicurati di aver scaricato il modello (es. ollama run nomic-embed-text)
        """
        self.embeddings_model = OllamaEmbeddings(model=model_name)

    def calculate_cosine_distances(self, sentences):
        distances = []
        for i in range(len(sentences) - 1):
            embedding_current = sentences[i]["combined_sentence_embedding"]
            embedding_next = sentences[i + 1]["combined_sentence_embedding"]

            # Calcola la similarità cosina
            similarity = cosine_similarity([embedding_current], [embedding_next])[0][0]

            # Converte in distanza cosina
            distance = 1 - similarity
            distances.append(distance)
            sentences[i]["distance_to_next"] = distance

        return distances, sentences

    def combine_sentences(self, sentences, buffer_size=1):
        for i in range(len(sentences)):
            combined_sentence = ""
            
            # Aggiunge le frasi PRECEDENTI in base al buffer_size
            for j in range(i - buffer_size, i):
                if j >= 0:
                    combined_sentence += sentences[j]["sentence"] + " "

            # Aggiunge la frase CORRENTE
            combined_sentence += sentences[i]["sentence"] + " "

            # Aggiunge le frasi SUCCESSIVE in base al buffer_size
            for j in range(i + 1, i + 1 + buffer_size):
                if j < len(sentences):
                    combined_sentence += sentences[j]["sentence"] + " "

            sentences[i]["combined_sentence"] = combined_sentence.strip()
        
        return sentences

    def create_chunks(self, text, buffer_size=1, percentile_threshold=95):
        """
        Funzione principale per eseguire lo chunking semantico sul testo.
        """
        # 1. Divide il testo in frasi singole
        single_sentences = re.split(r'(?<=[.?!])\s+', text.strip())
        sentences = [{"sentence": x, "index": i} for i, x in enumerate(single_sentences)]
        
        # 2. Combina le frasi con il buffer
        sentences = self.combine_sentences(sentences, buffer_size=buffer_size)
        
        # 3. Genera gli embeddings usando Ollama
        combined_text_list = [s["combined_sentence"] for s in sentences]
        embeddings = self.embeddings_model.embed_documents(combined_text_list)
        
        for i, emb in enumerate(embeddings):
            sentences[i]["combined_sentence_embedding"] = emb
            
        # 4. Calcola le distanze
        distances, sentences = self.calculate_cosine_distances(sentences)
        
        if not distances:
            return [text]
            
        # 5. Trova la soglia di taglio (es. 95esimo percentile delle distanze)
        breakpoint_threshold = np.percentile(distances, percentile_threshold)
        
        # 6. Unisce le frasi in chunk basandosi sulla soglia
        chunks = []
        current_chunk = ""
        
        for i in range(len(sentences)):
            current_chunk += sentences[i]["sentence"] + " "
            
            # Se la distanza supera la soglia, taglia e crea un nuovo chunk
            if i < len(sentences) - 1 and sentences[i]["distance_to_next"] > breakpoint_threshold:
                chunks.append(current_chunk.strip())
                current_chunk = ""
                
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks
