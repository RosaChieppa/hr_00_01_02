# document_processor.py
import os
import uuid
from hr_assistant.config import ImpostazioniSistema

class ElaboratoreDocumentiHR:
    @staticmethod
    def elabora_e_segmenta_file():
        """Scansiona la cartella risorse e divide i CV in blocchi semantici."""
        elenco_testi = []
        elenco_metadati = []
        elenco_id = []

        # Controllo di sicurezza se la cartella esiste
        if not os.path.exists(ImpostazioniSistema.CARTELLA_CURRICULA):
            return elenco_testi, elenco_metadati, elenco_id

        for nome_file in os.listdir(ImpostazioniSistema.CARTELLA_CURRICULA):
            if nome_file.endswith(".txt"):
                percorso_file = os.path.join(ImpostazioniSistema.CARTELLA_CURRICULA, nome_file)
                with open(percorso_file, 'r', encoding='utf-8') as flusso_file:
                    # Linearizziamo il testo prima dello split strutturale
                    frammenti_grezzi = flusso_file.read().replace('\n', '.').split('### ')

                    for frammento in frammenti_grezzi:
                        if not frammento.isspace() and not frammento == "":
                            elenco_testi.append(frammento.strip())
                            elenco_metadati.append({"source": nome_file})
                            elenco_id.append(f"rec_{uuid.uuid4()}")

        return elenco_testi, elenco_metadati, elenco_id

    @staticmethod
    def ottieni_intestazione_cv(percorso_reale, limite_righe=100):
        """Estrae le prime righe del file per consentire l'identificazione del candidato."""
        righe_lette = []
        if os.path.exists(percorso_reale):
            with open(percorso_reale, 'r', encoding='utf-8') as f:
                for contatore, riga in enumerate(f):
                    if contatore < limite_righe:
                        righe_lette.append(riga.strip())
                    else:
                        break
        return righe_lette
