import os
from sentence_transformers import SentenceTransformer

# 1. Scegli un modello (es. un ottimo modello multilingua/italiano)
nome_modello_huggingface = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

print(f"🔄 Scaricamento di {nome_modello_huggingface} da Hugging Face...")
model = SentenceTransformer(nome_modello_huggingface)

# 2. Definisci il percorso di destinazione (allineato alla tua struttura)
percorso_destinazione = os.path.join("modelli", "mio_modello")

# 3. Salva il modello. Questo genererà automaticamente tutte le cartelle 
# (1_Pooling, 2_Normalize, config.json, vocab.txt, ecc.)
print(f"💾 Salvataggio del modello in: {percorso_destinazione}")
model.save(percorso_destinazione)
print("✅ Modello creato e salvato con successo!")
