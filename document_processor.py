import os
import uuid
import hashlib
from datetime import datetime, timezone
import tempfile
import zipfile
import mimetypes
from typing import Tuple, List, Dict, Any

# Importazione per la lettura dei file PDF nativi
from pypdf import PdfReader

from config import ImpostazioniSistema
from semantic_chunking import SemanticChunking
from markitdown import MarkItDown

class ElaboratoreDocumentiHR:

    ESTENSIONI_SUPPORTATE = {
        ".txt": "text", ".pdf": "document", ".doc": "document", ".docx": "document",
        ".ppt": "presentation", ".pptx": "presentation", ".xls": "spreadsheet", 
        ".xlsx": "spreadsheet", ".html": "web", ".htm": "web", ".csv": "data", 
        ".json": "data", ".xml": "data", ".zip": "archive",
    }

    chunker_semantico = SemanticChunking()
    convertitore_testo = MarkItDown()

    @staticmethod
    def ottieni_hash_file(percorso_file: str) -> str:
        hash_md5 = hashlib.md5()
        with open(percorso_file, "rb") as f:
            for frammento in iter(lambda: f.read(4096), b""):
                hash_md5.update(frammento)
        return hash_md5.hexdigest()

    @staticmethod
    def ottieni_metadati_documento(percorso_file: str, nome_originale: str = None) -> Dict[str, Any]:
        nome_visualizzato = nome_originale if nome_originale else os.path.basename(percorso_file)
        estensione = os.path.splitext(nome_visualizzato)[1].lower()
        tipo_file = ElaboratoreDocumentiHR.ESTENSIONI_SUPPORTATE.get(estensione, "unknown")
        
        try:
            ultima_modifica = int(os.path.getmtime(percorso_file))
        except OSError:
            ultima_modifica = int(datetime.now(timezone.utc).timestamp())

        return {
            "hash": str(ElaboratoreDocumentiHR.ottieni_hash_file(percorso_file)),
            "last_modified": int(ultima_modifica),
            "source": str(nome_visualizzato),
            "file_type": str(tipo_file),
            "extension": str(estensione),
            "mime_type": str(mimetypes.guess_type(nome_visualizzato) or "application/octet-stream")
        }

    @staticmethod
    def estrai_testo_da_file(percorso_file: str) -> str:
        try:
            estensione = os.path.splitext(percorso_file)[1].lower()
            
            if estensione == ".pdf":
                testo_pdf = []
                reader = PdfReader(percorso_file)
                for pagina in reader.pages:
                    testo_pagina = pagina.extract_text()
                    if testo_pagina:
                        testo_pdf.append(testo_pagina)
                return "\n".join(testo_pdf)
                
            # CORRETTO: Sostituito resultado con risultato
            risultato = ElaboratoreDocumentiHR.convertitore_testo.convert(percorso_file)
            return risultato.text_content if risultato and risultato.text_content else ""
        except Exception as e:
            print(f"⚠️ Errore di estrazione su {percorso_file}: {e}")
            return ""

    @staticmethod
    def elabora_e_segmenta_singolo_file(percorso_file: str, nome_originale: str = None) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
        elenco_testi, elenco_metadati, elenco_id = [], [], []
        nome_file_effettivo = nome_originale if nome_originale else os.path.basename(percorso_file)
        estensione = os.path.splitext(nome_file_effettivo)[1].lower()

        if estensione == ".zip":
            return ElaboratoreDocumentiHR.elabora_archivio_zip(percorso_file)

        testo_completo = ElaboratoreDocumentiHR.estrai_testo_da_file(percorso_file)
        if not testo_completo.strip():
            return elenco_testi, elenco_metadati, elenco_id

        metadati_file = ElaboratoreDocumentiHR.ottieni_metadati_documento(percorso_file, nome_file_effettivo)
        
        frammenti_semantici = ElaboratoreDocumentiHR.chunker_semantico.create_chunks(
            text=testo_completo, buffer_size=1, percentile_threshold=90
        )

        for idx, frammento in enumerate(frammenti_semantici):
            testo_pulito = frammento.strip()
            if testo_pulito:
                elenco_testi.append(testo_pulito)
                
                metadato_chunk = metadati_file.copy()
                metadato_chunk["chunk_index"] = int(idx)
                metadato_chunk["total_chunks"] = int(len(frammenti_semantici))
                
                elenco_metadati.append(metadato_chunk)
                elenco_id.append(f"id_{metadati_file['hash']}_c{idx}")

        return elenco_testi, elenco_metadati, elenco_id

    @staticmethod
    def elabora_archivio_zip(percorso_zip: str) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
        tutti_testi, tutti_metadati, tutti_id = [], [], []
        nome_zip = os.path.basename(percorso_zip)

        with tempfile.TemporaryDirectory() as cartella_temp:
            try:
                with zipfile.ZipFile(percorso_zip, 'r') as archivio:
                    archivio.extractall(cartella_temp)
            except Exception as e:
                print(f"⚠️ Errore ZIP {percorso_zip}: {e}")
                return tutti_testi, tutti_metadati, tutti_id

            for radice, _, files in os.walk(cartella_temp):
                for file in files:
                    estensione = os.path.splitext(file)[1].lower()
                    if estensione in ElaboratoreDocumentiHR.ESTENSIONI_SUPPORTATE and estensione != ".zip":
                        percorso_completo = os.path.join(radice, file)
                        nome_file_virtuale = f"{nome_zip}/{file}"
                        
                        testi, metadati, ids = ElaboratoreDocumentiHR.elabora_e_segmenta_singolo_file(
                            percorso_file=percorso_completo, nome_originale=nome_file_virtuale
                        )
                        tutti_testi.extend(testi)
                        tutti_metadati.extend(metadati)
                        tutti_id.extend(ids)
        return tutti_testi, tutti_metadati, tutti_id

    @staticmethod
    def sincronizza_documenti(gestore_db) -> Tuple[int, int, int]:
        if not os.path.exists(ImpostazioniSistema.CARTELLA_CURRICULA):
            os.makedirs(ImpostazioniSistema.CARTELLA_CURRICULA, exist_ok=True)
            return 0, 0, 0

        file_correnti = {}
        for f in os.listdir(ImpostazioniSistema.CARTELLA_CURRICULA):
            estensione = os.path.splitext(f)[1].lower()
            if estensione in ElaboratoreDocumentiHR.ESTENSIONI_SUPPORTATE:
                percorso_completo = os.path.join(ImpostazioniSistema.CARTELLA_CURRICULA, f)
                file_correnti[f] = ElaboratoreDocumentiHR.ottieni_metadati_documento(percorso_completo)
        
        file_esistenti_db = gestore_db.ottieni_file_tracciati()
        
        file_da_aggiungere = set(file_correnti.keys()) - set(file_esistenti_db.keys())
        file_da_rimuovere = set(file_esistenti_db.keys()) - set(file_correnti.keys())
        file_da_aggiornare = {
            f for f in set(file_correnti.keys()) & set(file_esistenti_db.keys())
            if file_correnti[f]["hash"] != file_esistenti_db[f]["hash"]
        }

        contatore_aggiunti = 0
        contatore_aggiornati = 0
        contatore_rimossi = 0

        for nome_file in file_da_rimuovere:
            gestore_db.rimuovi_documento_per_sorgente(nome_file)
            contatore_rimossi += 1

        for action, file_selezionati in [("add", file_da_aggiungere), ("update", file_da_aggiornare)]:
            for nome_file in file_selezionati:
                percorso_file = os.path.join(ImpostazioniSistema.CARTELLA_CURRICULA, nome_file)
                testi, metadati, ids = ElaboratoreDocumentiHR.elabora_e_segmenta_singolo_file(percorso_file)
                
                if action == "update":
                    gestore_db.rimuovi_documento_per_sorgente(nome_file)
                    contatore_aggiornati += 1
                elif action == "add":
                    contatore_aggiunti += 1
                    
                if testi:
                    gestore_db.inserisci_documentazione(testi, metadati, ids)

        return contatore_aggiunti, contatore_aggiornati, contatore_rimossi
