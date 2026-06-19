import os
from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer, models

# 1. Prendi un modello Transformer generico (es. BERT italiano)
nome_base = "dbmdz/bert-base-italian-xxl-cased"
word_embedding_model = models.Transformer(nome_base, max_seq_length=256)

# 2. Crea esplicitamente il modulo di Pooling (quello che genera la cartella 1_Pooling)
# Specifichiamo 'mean' per fare la media dei token, proprio come nel tuo screenshot
pooling_model = models.Pooling(
    word_embedding_dimension=word_embedding_model.get_word_embedding_dimension(),
    pooling_mode_mean_tokens=True,
    pooling_mode_cls_token=False,
    pooling_mode_max_tokens=False
)

# 3. Crea il modulo di Normalizzazione (quello che genera la cartella 2_Normalize)
normalize_model = models.Normalize()

# 4. Unisci i pezzi in un unico oggetto SentenceTransformer
model = SentenceTransformer(modules=[word_embedding_model, pooling_model, normalize_model])

# 5. Salva su disco per generare l'alberatura dei file
percorso_destinazione = os.path.join("modelli", "mio_modello_personalizzato")
model.save(percorso_destinazione)
print(f"✅ Struttura personalizzata creata in {percorso_destinazione}")
