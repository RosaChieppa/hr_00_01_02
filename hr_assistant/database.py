import chromadb
from typing import Dict, Any, List

from config import ImpostazioniSistema
from custom_embeddings import CustomEmbeddingFunction

class GestoreDatabaseVettoriale:
    def __init__(self):
        self.funzione_embedding = CustomEmbeddingFunction()
        self.client_locale = chromadb.PersistentClient(path=ImpostazioniSistema.PERCORSO_PERSISTENZA_DB)
        
        self.collezione_dati = self.client_locale.get_or_create_collection(
            name=ImpostazioniSistema.NOME_COLLEZIONE, 
            embedding_function=self.funzione_embedding,
            metadata={"hnsw:space": "cosine"}
        )

    def inserisci_documentazione(self, testi_cv: List[str], metadati_file: List[Dict[str, Any]], codici_id: List[str]):
        """Aggiunge i segmenti estratti nella collezione vettoriale."""
        if testi_cv:
            print("💾 Popolamento o aggiornamento del database vettoriale locale...")
            self.collezione_dati.add(documents=testi_cv, metadatas=metadati_file, ids=codici_id)
            print(f"✅ Elementi totali nella collezione: {self.collezione_dati.count()}")

    def effettua_ricerca_semantica(self, testo_ricerca: str, numero_risultati: int = 1):
        """Interroga la collezione per similarità semantica rispetto alla query."""
        # CORRETTO: allineato il parametro interno a numero_risultati
        return self.collezione_dati.query(query_texts=[testo_ricerca], n_results=numero_risultati)

    def ottieni_file_tracciati(self) -> Dict[str, Dict[str, Any]]:
        """Recupera tutti i file univoci e i loro metadati."""
        risultato = self.collezione_dati.get(include=["metadatas"])
        file_tracciati = {}

        # CORRETTO: raddrizzato il secondo termine in 'risultato'
        if risultato and risultato.get("metadatas"):
            for metadato in risultato["metadatas"]:
                if metadato and "source" in metadato:
                    sorgente = metadato["source"]
                    if sorgente not in file_tracciati:
                        file_tracciati[sorgente] = {
                            "hash": metadato.get("hash"),
                            "last_modified": metadato.get("last_modified"),
                            "source": sorgente,
                        }
        return file_tracciati

    def rimuovi_documento_per_sorgente(self, sorgente: str):
        """Rimuove tutte le voci del database associate a uno specifico file sorgente."""
        risultato = self.collezione_dati.get(where={"source": sorgente}, include=[])
        if risultato and risultato.get("ids"):
            self.collezione_dati.delete(ids=risultato["ids"])
            print(f"🗑️ Rimossi segmenti per il file: {sorgente}")

    def svuota_database(self):
        """Cancella l'intera collezione e la ricrea vuota."""
        try:
            self.client_locale.delete_collection(name=ImpostazioniSistema.NOME_COLLEZIONE)
        except Exception:
            pass 
        
        self.collezione_dati = self.client_locale.get_or_create_collection(
            name=ImpostazioniSistema.NOME_COLLEZIONE, 
            embedding_function=self.funzione_embedding,
            metadata={"hnsw:space": "cosine"}
        )
        print("✨ Database azzerato con successo.")

    def ottieni_statistiche(self) -> str:
        """Estrae i metadati della collezione calcolando i file reali elaborati."""
        risultato = self.collezione_dati.get(include=["metadatas"])
        if risultato and risultato.get("metadatas"):
            valori_distinti = set(d["source"] for d in risultato["metadatas"] if d and "source" in d)
            numero_files = len(valori_distinti)
        else:
            numero_files = 0

        return f"""
            Nome Collezione: {self.collezione_dati.name}
            Numero totale Frammenti indicizzati: {self.collezione_dati.count()}
            Numero File unici elaborati: {numero_files}
        """
