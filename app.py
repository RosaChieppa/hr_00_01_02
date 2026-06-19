import os
import sys
import asyncio
import shutil

# Risolve i problemi di ciclo di eventi asincroni su sistemi Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import chainlit as cl

# Import dei moduli core reali
from document_processor import ElaboratoreDocumentiHR
from database import GestoreDatabaseVettoriale
from config import ImpostazioniSistema
from utils import AssistenteModelloLinguistico

# Inizializzazione dei moduli core
db = GestoreDatabaseVettoriale()
dp = ElaboratoreDocumentiHR()


@cl.on_chat_start
async def start():
    # Sincronizzazione iniziale asincrona all'avvio della chat per evitare freeze del server
    msg = await cl.Message(author="system_assistant", content="🔄 Sincronizzazione iniziale del database in corso...").send()
    added, updated, removed = await asyncio.to_thread(dp.sincronizza_documenti, db)
    
    # Pulsanti di azione per la gestione del DB
    actions = [
        cl.Action(name="db_stats", icon="database", payload={"value": "db_stats"}, label="Statistiche DB"),
        cl.Action(name="db_reindex", icon="refresh-cw", payload={"value": "db_reindex"}, label="Sincronizza/Reindex"),
        cl.Action(name="db_remove", icon="trash-2", payload={"value": "db_remove"}, label="Svuota DB"),
    ]

    msg.content = f"✅ Sistema Pronto! Sincronizzazione iniziale completata ({added} aggiunti, {updated} aggiornati, {removed} rimossi)."
    msg.actions = actions
    await msg.update()

    cl.user_session.set(
        "messages",
        [
            {
                "role": "system",
                "content": (
                    "Sei un assistente specializzato nel mondo HR (Risorse Umane). "
                    "Rispondi in modo professionale, sintetico e pragmatico. "
                    "Il tuo ruolo principale è analizzare i curricula forniti nel contesto e individuare "
                    "il candidato ideale rispetto alle richieste del recruiter."
                ),
            }
        ],
    )


@cl.action_callback("db_stats")
async def on_action_db_stats(action: cl.Action):
    db_info = await asyncio.to_thread(db.ottieni_statistiche)
    response = await AssistenteModelloLinguistico.ottieni_statistiche_db(db_info)
    await cl.Message(author="system_assistant", content=response).send()


@cl.action_callback("db_reindex")
async def on_action_db_reindex(action: cl.Action):
    msg = await cl.Message(author="system_assistant", content="⏳ Reindicizzazione in corso... attendere.").send()
    added, updated, removed = await asyncio.to_thread(dp.sincronizza_documenti, db)
    msg.content = f"✅ DB reindicizzato con successo. Sincronizzazione: {added} aggiunti, {updated} aggiornati, {removed} rimossi."
    await msg.update()


@cl.action_callback("db_remove")
async def on_action_db_remove(action: cl.Action):
    await asyncio.to_thread(db.svuota_database)
    message = "🗑️ Il database è stato completamente svuota. È necessario lanciare la sincronizzazione dei documenti."
    await cl.Message(author="system_assistant", content=message).send()


def _sincronizza_singolo_file_sync(file_path, file_name):
    """Funzione di supporto sincrona per elaborazione ed inserimento su VectorDB"""
    documents, metadatas, ids = dp.elabora_e_segmenta_singolo_file(file_path)
    if documents:
        db.inserisci_documentazione(documents, metadatas, ids)
        return f"✅ File '{file_name}' caricato e indicizzato con successo."
    return f"❌ Errore nel processare il file '{file_name}'."


async def _file_upload(file) -> str:
    file_name = file.name
    dst_file_path = os.path.join(ImpostazioniSistema.CARTELLA_CURRICULA, file_name)
    src_file_path = file.path
    
    await asyncio.to_thread(os.makedirs, ImpostazioniSistema.CARTELLA_CURRICULA, exist_ok=True)
    await asyncio.to_thread(shutil.copy, src_file_path, dst_file_path)
    
    return await asyncio.to_thread(_sincronizza_singolo_file_sync, dst_file_path, file_name)


@cl.on_message
async def handle_message(message: cl.Message):
    # 1. Gestione live dei file caricati (Drag & Drop)
    if message.elements:
        status_msg = await cl.Message(author="system_assistant", content="Caricamento e indicizzazione documenti in corso...").send() 
        files = [el for el in message.elements if isinstance(el, cl.File)]

        tasks = [_file_upload(file) for file in files]
        results = await asyncio.gather(*tasks)

        status_msg.content = "\n".join(results)
        await status_msg.update()        

        if not message.content or message.content.strip() == "":
            return

    # 2. Interrogazione del sistema tramite Ricerca Semantica RAG
    user_question = message.content
    
    # Eseguiamo la query sul VectorDB
    results = await asyncio.to_thread(db.effettua_ricerca_semantica, user_question, numero_risultati=3)

    # Controllo di sicurezza sui risultati del DB vettoriale
    if not results or "documents" not in results or not results["documents"] or len(results["documents"][0]) == 0:
        await cl.Message(author="hr_assistant", content="Non ho trovato informazioni rilevanti nei curricula disponibili per rispondere a questa richiesta.").send()
        return

    # Costruzione dinamica del contesto unendo tutti i chunk trovati
    context_chunks = []
    fonti_utilizzate = set()
    
    # Iteriamo sui documenti estratti da ChromaDB (struttura a lista nidificata [[chunk1, chunk2]])
    for i in range(len(results["documents"][0])):
        text_chunk = results["documents"][0][i]
        meta = results["metadatas"][0][i] if (results.get("metadatas") and results["metadatas"]) else {}
        
        source_file = meta.get("source", "Documento Sconosciuto")
        fonti_utilizzate.add(source_file)
        context_chunks.append(f"--- Frammento da {source_file} ---\n{text_chunk}")

    full_context = "\n\n".join(context_chunks)

    # Estrazione dell'anagrafica del candidato asincrona nativa
    candidate_name = await AssistenteModelloLinguistico.estrai_nominativo_candidato(full_context[:1500])

    # Generazione del prompt iniettando il contesto completo multi-documento
    prompt = AssistenteModelloLinguistico.genera_prompt_strutturato(full_context, user_question, candidate_name)

    messages = cl.user_session.get("messages", [])
    messages.append({"role": "user", "content": prompt})

    response_message = cl.Message(author="hr_assistant", content="")
    await response_message.send()

    try:
        # Chiamata allo stream asincrono del modello linguistico locale
        async for token in AssistenteModelloLinguistico.genera_risposta_stream(messages):
            if token:
                await response_message.stream_token(str(token))

        # Mostra le fonti utilizzate in fondo alla risposta per trasparenza HR
        fonti_str = ", ".join(fonti_utilizzate)
        response_message.content += f"\n\n*📄 Fonti consultate: {fonti_str}*"
        
        # Ripristino della cronologia pulita (salviamo la domanda pulita e non il mega prompt)
        messages.pop()
        messages.append({"role": "user", "content": user_question})
        messages.append({"role": "assistant", "content": response_message.content})
        await response_message.update()

    except Exception as e:
        error_message = f"Si è verificato un errore durante la generazione della risposta: {str(e)}"
        await cl.Message(author="hr_assistant", content=error_message).send()
        print(f"Errore LLM: {error_message}")

    cl.user_session.set("messages", messages)
