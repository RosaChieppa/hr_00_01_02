# document_processor.py
import os
import uuid
import hashlib
from hr_assistant.config import ImpostazioniSistema

class ElaboratoreDocumentiHR:

    @staticmethod
    def ottieni_hash_file(percorso_file):
        """Calcola l'hash MD5 del contenuto di un file per tracciarne le modifiche."""
        hash_md5 = hashlib.md5()
        with open(percorso_file, "rb") as f:
            for frammento in iter(lambda: f.read(4096), b""):
                hash_md5.update(frammento)
        return hash_md5.hexdigest()

    @staticmethod
    def ottieni_metadati_documento(percorso_file):
        """Genera i metadati del documento inclusi hash, ultima modifica e nome file sorgente."""
        return {
            "hash": ElaboratoreDocumentiHR.ottieni_hash_file(percorso_file),
            "last_modified": os.path.getmtime(percorso_file),
            "source": os.path.basename(percorso_file),
        }

    @staticmethod
    def elabora_e_segmenta_singolo_file(percorso_file):
        """Processa un singolo documento dividendolo in blocchi standard usando il separatore."""
        elenco_testi = []
        elenco_metadati = []
        elenco_id = []

        with open(percorso_file, 'r', encoding='utf-8') as flusso_file:
            testo_completo = flusso_file.read()
            
            # Suddivisione logica dei frammenti sostituendo i ritorni a capo per stabilità dell'LLM
            testo_normalizzato = testo_completo.replace("\n", ".")
            frammenti_grezzi = testo_normalizzato.split('### ')
            metadati_file = ElaboratoreDocumentiHR.ottieni_metadati_documento(percorso_file)

            for contatore, frammento in enumerate(frammenti_grezzi):
                testo_pulito = frammento.strip()
                if testo_pulito:
                    if contatore > 0 or testo_completo.startswith('### '):
                        testo_pulito = f"### {testo_pulito}"
                        
                    elenco_testi.append(testo_pulito)
                    elenco_metadati.append(metadati_file)
                    elenco_id.append(f"rec_{uuid.uuid4()}")

        return elenco_testi, elenco_metadati, elenco_id

    @staticmethod
    def sincronizza_documenti(gestore_db):
        """Scansiona la cartella risorse e sincronizza lo stato dei file sul database vettoriale."""
        if not os.path.exists(ImpostazioniSistema.CARTELLA_CURRICULA):
            print(f"⚠️ Attenzione: La cartella {ImpostazioniSistema.CARTELLA_CURRICULA} non esiste!")
            return 0, 0, 0

        # Mappatura dei file locali correnti
        file_correnti = {
            f: ElaboratoreDocumentiHR.ottieni_metadati_documento(
                os.path.join(ImpostazioniSistema.CARTELLA_CURRICULA, f)
            )
            for f in os.listdir(ImpostazioniSistema.CARTELLA_CURRICULA) if f.endswith(".txt")
        }
        
        # Mappatura dei file censiti sul DB vettoriale
        file_esistenti_db = gestore_db.ottieni_file_tracciati()

        # Calcolo dei set operativi
        file_da_aggiungere = set(file_correnti.keys()) - set(file_esistenti_db.keys())
        file_da_rimuovere = set(file_esistenti_db.keys()) - set(file_correnti.keys())
        file_da_aggiornare = {
            f
            for f in set(file_correnti.keys()) & set(file_esistenti_db.keys())
            if file_correnti[f]["hash"] != file_esistenti_db[f]["hash"]
        }

        # Elaborazione delle aggiunte e delle modifiche
        for azione, file_selezionati in [("add", file_da_aggiungere), ("update", file_da_aggiornare)]:
            for nome_file in file_selezionati:
                percorso_file = os.path.join(ImpostazioniSistema.CARTELLA_CURRICULA, nome_file)
                # Chiamata corretta al metodo statico interno
                testi, metadati, ids = ElaboratoreDocumentiHR.elabora_e_segmenta_singolo_file(percorso_file)

                if azione == "update":
                    gestore_db.rimuovi_documento_per_sorgente(nome_file)

                if testi:
                    gestore_db.inserisci_documentazione(testi, metadati, ids)

        # Rimozione dei file non più presenti localmente
        for nome_file in file_da_rimuovere:
            gestore_db.rimuovi_documento_per_sorgente(nome_file)

        return len(file_da_aggiungere), len(file_da_aggiornare), len(file_da_rimuovere)

    # NUOVA INTEGRAZIONE: Metodo read_first_lines ottimizzato con zip e allineato con lo stile attuale
    @staticmethod
    def ottieni_intestazione_cv(percorso_reale, limite_righe=10):
        """Estrae le prime righe del file usando zip per massimizzare le prestazioni ed evitare overload di memoria."""
        if os.path.exists(percorso_reale):
            with open(percorso_reale, 'r', encoding='utf-8') as f:
                righe_lette = [line.strip() for line, _ in zip(f, range(limite_righe))]
                return " ".join(righe_lette)
        return ""
