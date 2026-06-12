import os
import chainlit as cl
from hr_assistant.document_processor import ElaboratoreDocumentiHR
from hr_assistant.database import GestoreDatabaseVettoriale
from hr_assistant.config import ImpostazioniSistema
from hr_assistant.utils import AssistenteModelloLinguistico

# --- FASE INIZIALE: ELABORAZIONE E INDICIZZAZIONE ---
# Estrazione dei segmenti informativi dai curricula locali
testi_cv, metadati_file, codici_id = ElaboratoreDocumentiHR.elabora_e_segmenta_file()

# Inizializzazione del database vettoriale persistente e caricamento dati
istanza_db = GestoreDatabaseVettoriale()
istanza_db.inserisci_documentazione(testi_cv, metadati_file, codici_id)


@cl.on_chat_start
def inizializza_conversazione():
    """Configura il prompt di sistema iniziale per indirizzare il comportamento dell'AI."""
    cl.user_session.set(
        "cronologia_principale",
        [
            {
                "role": "system",
                "content": """
                    Agisci come un consulente HR senior e un selezionatore esperto. Fornisci risposte mirate, 
                    professionali e basate esclusivamente sulle evidenze documentali per identificare il candidato ideale.
                """,
            }
        ],
    )


@cl.on_message
async def gestisci_richiesta_chat(message: cl.Message):
    """Orchestra la ricezione del messaggio, l'interrogazione RAG e lo streaming della risposta."""
    quesito_utente = message.content
    
    # Esecuzione della ricerca semantica sulla collezione
    risultati_ricerca = istanza_db.effettua_ricerca_semantica(quesito_utente)

    # RISOLUZIONE BUG: Estrazione sicura dei dati dai metadati e dai documenti di ChromaDB
    file_selezionato = risultati_ricerca["metadatas"][0]["source"]
    testo_estratto_rilevante = risultati_ricerca["documents"][0]

    # Recupero delle linee iniziali del file per l'anagrafica
    percorso_file_origine = os.path.join(ImpostazioniSistema.CARTELLA_CURRICULA, file_selezionato)
    righe_anagrafica = ElaboratoreDocumentiHR.ottieni_intestazione_cv(percorso_file_origine, 10)

    # Ricostruzione del blocco di contesto per l'LLM
    contesto_documentale = f"CONTESTO APPLICATIVO: nome file sorgente {file_selezionato} | estratto del profilo: {testo_estratto_rilevante}"

    # Identificazione asincrona del nome tramite LLM
    nome_candidato = await AssistenteModelloLinguistico.estrai_nominativo_candidato(righe_anagrafica)

    # Generazione del prompt finale arricchito con vincoli e contesto
    prompt_ingegnerizzato = AssistenteModelloLinguistico.genera_prompt_strutturato(
        contesto_documentale, quesito_utente, nome_candidato
    )

    # Recupero della cronologia della sessione corrente
    storico_chat = cl.user_session.get("cronologia_messaggi", [])
    storico_chat.append({"role": "user", "content": prompt_ingegnerizzato})

    # Inizializzazione del contenitore per lo streaming dell'output su Chainlit
    messaggio_risposta_interattiva = cl.Message(content="")
    await messaggio_risposta_interattiva.send()

    try:
        # Richiesta del flusso generativo in streaming
        flusso_completamento = AssistenteModelloLinguistico.esegui_flusso_chat(storico_chat)

        for frammento in flusso_completamento:
            # Controllo di sicurezza per evitare errori su token vuoti o di sistema
            if frammento.choices[0].delta.content:
                await messaggio_risposta_interattiva.stream_token(str(frammento.choices[0].delta.content))

        storico_chat.append({"role": "assistant", "content": messaggio_risposta_interattiva.content})
        await messaggio_risposta_interattiva.update()

    except Exception as eccezione_runtime:
        notifica_errore = f"Si è verificato un problema di elaborazione: {str(eccezione_runtime)}"
        await cl.Message(content=notifica_errore).send()
        print(notifica_errore)

    cl.user_session.set("cronologia_messaggi", storico_chat)
