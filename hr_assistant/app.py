import os
import sys
import asyncio
import shutil

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import chainlit as cl

from document_processor import ElaboratoreDocumentiHR
from database import GestoreDatabaseVettoriale
from config import ImpostazioniSistema
from utils import AssistenteModelloLinguistico

istanza_db = None

@cl.action_callback("db_stats")
async def gestisci_statistiche_db(action: cl.Action):
    global istanza_db
    if istanza_db:
        info_db = istanza_db.ottieni_statistiche()
        risposta = await AssistenteModelloLinguistico.ottieni_statistiche_db(info_db)
        await cl.Message(risposta).send()

@cl.action_callback("db_reindex")
async def gestisci_reindicizzazione_db(action: cl.Action):
    global istanza_db
    if istanza_db:
        msg_avviso = cl.Message(content="🔄 Reindicizzazione in corso...")
        await msg_avviso.send()
        
        loop = asyncio.get_running_loop()
        aggiunti, aggiornati, rimossi = await loop.run_in_executor(
            None, ElaboratoreDocumentiHR.sincronizza_documenti, istanza_db
        )
        await msg_avviso.remove()
        await cl.Message(f"🔄 Sincronizzazione completata: {aggiunti} aggiunti, {aggiornati} modificati, {rimossi} rimossi.").send()

@cl.action_callback("db_clear")
async def gestisci_svuotamento_db(action: cl.Action):
    global istanza_db
    if istanza_db:
        istanza_db.svuota_database()
        await cl.Message("🗑️ Il database vettoriale è stato completamente svuotato.").send()

@cl.on_chat_start
async def inizializza_conversazione():
    global istanza_db
    msg_avvio = cl.Message(content="🤖 Avvio dell'assistente HR in corso...")
    await msg_avvio.send()
    
    if istanza_db is None:
        msg_avvio.content = "🔍 Inizializzazione del Database Vettoriale e Controllo File..."
        await msg_avvio.update()
        istanza_db = GestoreDatabaseVettoriale()
        
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, ElaboratoreDocumentiHR.sincronizza_documenti, istanza_db)

    await msg_avvio.remove()

    azioni = [
        cl.Action(name="db_stats", icon="bar-chart-2", payload={"value": "stats"}, label="📊 Statistiche"),
        cl.Action(name="db_reindex", icon="refresh-cw", payload={"value": "reindex"}, label="🔄 Sincronizza"),
        cl.Action(name="db_clear", icon="trash-2", payload={"value": "clear"}, label="🗑️ Azzera DB")
    ]
    await cl.Message(content="📋 Pannello di controllo assistente RAG pronto:", actions=azioni).send()
    cl.user_session.set("cronologia_messaggi", [])

@cl.on_message
async def gestisci_richiesta_chat(message: cl.Message):
    global istanza_db
    if istanza_db is None:
        await cl.Message(content="Database non pronto. Attendi...").send()
        return

    # --- TRATTAMENTO LIVE DEI FILE (DRAG & DROP) ---
    if message.elements:
        files = [el for el in message.elements if isinstance(el, cl.File)]
        for f in files:
            nome_sanificato = f.name.replace(" ", "_")
            percorso_salvataggio = os.path.join(ImpostazioniSistema.CARTELLA_CURRICULA, nome_sanificato)
            try:
                shutil.copy(f.path, percorso_salvataggio)
                loop = asyncio.get_running_loop()
                testi, metadati, ids = await loop.run_in_executor(
                    None, ElaboratoreDocumentiHR.elabora_e_segmenta_singolo_file, percorso_salvataggio
                )
                if testi:
                    istanza_db.inserisci_documentazione(testi, metadati, ids)
                    await cl.Message(content=f"✅ `{nome_sanificato}` caricato ed indicizzato.").send()
            except Exception as e:
                await cl.Message(content=f"❌ Errore file `{nome_sanificato}`: {str(e)}").send()
        if not message.content:
            return

    # --- RICERCA SEMANTICA E RISPOSTA RAG ---
    quesito_utente = message.content
    risultati = istanza_db.effettua_ricerca_semantica(quesito_utente, numero_risultati=3)

    if not risultati or "documents" not in risultati or not risultati["documents"] or not risultati["documents"][0]:
        context = "Nessuna informazione rilevante trovata nei curricula."
        nome_candidato = "Sconosciuto"
    else:
        frammenti = risultati["documents"][0]
        context = "\n---\n".join(frammenti)
        nome_candidato = await AssistenteModelloLinguistico.estrai_nominativo_candidato(context[:400])

    prompt_rag = AssistenteModelloLinguistico.genera_prompt_strutturato(
        testo_contesto=context, quesito_utente=quesito_utente, nome_candidato=nome_candidato
    )

    cronologia = cl.user_session.get("cronologia_messaggi", [])
    cronologia.append({"role": "user", "content": prompt_rag})

    msg_risposta = cl.Message(content="")
    await msg_risposta.send()

    try:
        async for chunk in AssistenteModelloLinguistico.genera_risposta_stream(cronologia):
            await msg_risposta.stream_token(chunk)
        await msg_risposta.update()
        
        # Pulizia memoria storica per i turni successivi
        cronologia.pop()
        cronologia.append({"role": "user", "content": quesito_utente})
        cronologia.append({"role": "assistant", "content": msg_risposta.content})
        cl.user_session.set("cronologia_messaggi", cronologia)
    except Exception as e:
        await cl.Message(content=f"❌ Errore generazione: {str(e)}").send()
