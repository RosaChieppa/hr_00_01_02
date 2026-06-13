# document_processor.py
import os
import uuid
from hr_assistant.config import ImpostazioniSistema

class ElaboratoreDocumentiHR:
    @staticmethod
    def elabora_e_segmenta_file():
        """Scansiona la cartella risorse e divide i CV in blocchi standard usando il separatore."""
        elenco_testi = []
        elenco_metadati = []
        elenco_id = []

        # Controllo di sicurezza se la cartella esiste
        if not os.path.exists(ImpostazioniSistema.CARTELLA_CURRICULA):
            print(f"⚠️ Attenzione: La cartella {ImpostazioniSistema.CARTELLA_CURRICULA} non esiste!")
            return elenco_testi, elenco_metadati, elenco_id

        for nome_file in os.listdir(ImpostazioniSistema.CARTELLA_CURRICULA):
            if nome_file.endswith(".txt"):
                percorso_file = os.path.join(ImpostazioniSistema.CARTELLA_CURRICULA, nome_file)
                with open(percorso_file, 'r', encoding='utf-8') as flusso_file:
                    testo_completo = flusso_file.read()
                    
                    # Suddivisione richiesta dal docente
                    frammenti_grezzi = testo_completo.split('### ')

                    for contatore, frammento in enumerate(frammenti_grezzi):
                        testo_pulito = frammento.strip()
                        if testo_pulito:
                            # Preserva la formattazione dei tag per dare contesto a Ollama
                            if contatore > 0 or testo_completo.startswith('### '):
                                testo_pulito = f"### {testo_pulito}"
                                
                            elenco_testi.append(testo_pulito)
                            elenco_metadati.append({"source": nome_file})
                            elenco_id.append(f"rec_{uuid.uuid4()}")

        return elenco_testi, elenco_metadati, elenco_id

    @staticmethod
    def ottieni_intestazione_cv(percorso_reale, limite_righe=10):
        """Estrae le prime righe del file per consentire l'identificazione del candidato."""
        righe_lette = []
        if os.path.exists(percorso_reale):
            with open(percorso_reale, 'r', encoding='utf-8') as f:
                for contatore, riga in enumerate(f):
                    if contatore < limite_righe:
                        righe_lette.append(riga.strip())
                    else:
                        break
        return " ".join(righe_lette)
