# __init__.py
import os
import asyncio

# PATCH CRITICA PER PYTHON 3.14: Forziamo la creazione del loop asincrono prima del server
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

import chainlit as cl
from hr_assistant.document_processor import ElaboratoreDocumentiHR
from hr_assistant.database import GestoreDatabaseVettoriale
from hr_assistant.config import ImpostazioniSistema
from hr_assistant.utils import AssistenteModelloLinguistico

# Dichiariamo la variabile globale per il database
istanza_db = None

@cl.on_chat_start
async def inizializza_conversazione():
    """Inizializza il database vettoriale all'interno del loop asincrono e imposta la cronologia."""
    global istanza_db
    
    if istanza_db is None:
        print("🔍 Controllo e indicizzazione dei curricula...")
        testi_cv, metadati_file, codici_id = ElaboratoreDocumentiHR.elabora_e_segmenta_file()
        istanza_db = GestoreDatabaseVettoriale()
        istanza_db.inserisci_documentazione(testi_cv, metadati_file, codici_id)

    messaggio_sistema = {
        "role": "system",
        "content": (
            "Agisci come un consulente HR senior e un selezionatore esperto. Fornisci risposte mirate, "
            "professionali e basate esclusivamente sulle evidenze documentali per identificare il candidato ideale."
        ),
    }
    cl.user_session.set("cronologia_messaggi", [messaggio_sistema])


@cl.on_message
async def gestisci_richiesta_chat(message: cl.Message):
    """Orchestra la ricezione del messaggio, l'interrogazione RAG locale e lo streaming con Ollama."""
    global istanza_db
    quesito_utente = message.content
    
    if istanza_db is None:
        await cl.Message(content="Il database non è pronto. Attendi un istante e riprova.").send()
        return

    try:
        # Esecuzione della ricerca semantica sulla collezione ChromaDB locale
        risultati_ricerca = istanza_db.effettua_ricerca_semantica(quesito_utente)

        # Verifica di sicurezza: blocca l'esecuzione se il database non ha prodotto risultati
        if not risultati_ricerca or not risultati_ricerca.get("documents") or not risultati_ricerca["documents"][0]:
            await cl.Message(content="Mi dispiace, non ho trovato informazioni pertinenti nei curricula archiviati.").send()
            return

        # RISOLUZIONE DEL BLOCCO: Estrazione sicura usando i doppi indici per le liste annidate di ChromaDB
        file_selezionato = risultati_ricerca["metadatas"][0][0]["source"]
        testo_estratto_rilevante = risultati_ricerca["documents"][0][0]

        # Recupero delle linee iniziali del file per l'anagrafica
        percorso_file_origine = os.path.join(ImpostazioniSistema.CARTELLA_CURRICULA, file_selezionato)
        righe_anagrafica = ElaboratoreDocumentiHR.ottieni_intestazione_cv(percorso_file_origine, 10)

        # Ricostruzione del blocco di contesto per l'LLM locale
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

        # Chiamata asincrona nativa e streaming dei token
        async for token in AssistenteModelloLinguistico.esegui_flusso_chat(storico_chat):
            if token:
                await messaggio_risposta_interattiva.stream_token(str(token))

        storico_chat.append({"role": "assistant", "content": messaggio_risposta_interattiva.content})
        await messaggio_risposta_interattiva.update()
        cl.user_session.set("cronologia_messaggi", storico_chat)

    except Exception as eccezione_runtime:
        notifica_errore = f"Si è verificato un problema durante l'elaborazione: {str(eccezione_runtime)}"
        await cl.Message(content=notifica_errore).send()
        print(notifica_errore)
