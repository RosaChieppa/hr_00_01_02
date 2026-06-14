# __init__.py
import os
import sys
import asyncio

# Configurazione del loop asincrono ottimale per ambienti Windows con Python 3.12
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import chainlit as cl
from hr_assistant.document_processor import ElaboratoreDocumentiHR
from hr_assistant.database import GestoreDatabaseVettoriale
from hr_assistant.config import ImpostazioniSistema
from hr_assistant.utils import AssistenteModelloLinguistico

# Dichiariamo la variabile globale per il database
istanza_db = None


# --- GESTIONE DELLE AZIONI INTERATTIVE (CALLBACKS) ---

@cl.action_callback("db_stats")
async def gestisci_statistiche_db(action: cl.Action):
    """Callback per recuperare e mostrare le statistiche del database tramite LLM."""
    global istanza_db
    if istanza_db:
        # Chiamata al nuovo metodo integrato nel modulo database
        info_db = istanza_db.ottieni_statistiche()
        # Genera la risposta strutturata o formattata tramite l'LLM helper
        risposta = await AssistenteModelloLinguistico.ottieni_statistiche_db(info_db)
        await cl.Message(risposta).send()
    else:
        await cl.Message("Database non inizializzato.").send()


@cl.action_callback("db_reindex")
async def gestisci_reindicizzazione_db(action: cl.Action):
    """Callback per forzare il rinfresco e la sincronizzazione manuale dei file txt."""
    global istanza_db
    if istanza_db:
        aggiunti, aggiornati, rimossi = ElaboratoreDocumentiHR.sincronizza_documenti(istanza_db)
        messaggio = (
            f"🔄 Database reindicizzato con successo.\n"
            f"Sincronizzazione completata: {aggiunti} aggiunti, {aggiornati} modificati, {rimossi} rimossi."
        )
        await cl.Message(messaggio).send()
    else:
        await cl.Message("Impossibile reindicizzare: database non pronto.").send()


@cl.action_callback("say_hello")
async def gestisci_saluto(action: cl.Action):
    """Callback dimostrativo di saluto basato sul payload."""
    valore_payload = action.payload.get("value", "utente")
    await cl.Message(f"Ciao {valore_payload}! Come posso aiutarti oggi?").send()


# --- CONFIGURAZIONE LOGICHE DI CHAT ---

@cl.on_chat_start
async def inizializza_conversazione():
    """Inizializza il database vettoriale all'interno del loop asincrono e imposta la cronologia."""
    global istanza_db
    
    if istanza_db is None:
        print("🔍 Controllo e sincronizzazione avanzata dei curricula...")
        istanza_db = GestoreDatabaseVettoriale()
        
        # Sincronizzazione atomica bidirezionale locale -> DB vettoriale
        aggiunti, aggiornati, rimossi = ElaboratoreDocumentiHR.sincronizza_documenti(istanza_db)
        print(f"Sincronizzazione completata: {aggiunti} aggiunti, {aggiornati} modificati, {rimossi} rimossi.")

    # Aggiunta dei pulsanti di azione interattivi visibili in cima alla chat
    azioni_disponibili = [
        cl.Action(
            name="db_stats",
            icon="mouse-pointer-click",
            payload={"value": "db_stats"},
            label="📊 Statistiche Database",
        ),
        cl.Action(
            name="db_reindex",
            icon="mouse-pointer-click",
            payload={"value": "db_reindex"},
            label="🔄 Reindex Database",
        )
    ]

    await cl.Message(content="📋 Informazioni e utilità del sistema HR:", actions=azioni_disponibili).send()

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
        # Esecuzione della ricerca semantica sulla collezione ChromaDB locale (recuperando fino a 3 frammenti significativi)
        risultati_ricerca = istanza_db.effettua_ricerca_semantica(quesito_utente, numero_risultati=3)

        # Verifica di sicurezza: blocca l'esecuzione se il database non ha prodotto risultati pertinenti
        if not risultati_ricerca or not risultati_ricerca.get("documents") or not risultati_ricerca["documents"] or not risultati_ricerca["documents"][0]:
            await cl.Message(content="Mi dispiace, non ho trovato informazioni pertinenti nei curricula archiviati.").send()
            return

        # Estrazione sicura usando i doppi indici per le liste annidate restituite da ChromaDB
        file_selezionato = risultati_ricerca["metadatas"][0][0]["source"]
        testo_estratto_rilevante = risultati_ricerca["documents"][0][0]

        # Estrazione delle prime 10 righe del file sorgente per recuperare l'anagrafica iniziale
        percorso_completo_file = os.path.join(ImpostazioniSistema.CARTELLA_CURRICULA, file_selezionato)
        informazioni_anagrafiche = ElaboratoreDocumentiHR.ottieni_intestazione_cv(percorso_completo_file, limite_righe=10)

        # Ricostruzione strutturata del blocco di contesto completo per l'LLM
        contesto_documentale = (
            f"CONTESTO APPLICATIVO: nome file sorgente {file_selezionato} | "
            f"estratto del profilo significativo: {testo_estratto_rilevante} | "
            f"informazioni generali del candidato: {informazioni_anagrafiche}"
        )

        # Generazione del prompt ingegnerizzato
        prompt_ingegnerizzato = AssistenteModelloLinguistico.genera_prompt_strutturato(
            contesto_documentale, quesito_utente, file_selezionato
        )

        # Recupero e aggiornamento dello storico della conversazione corrente
        storico_chat = cl.user_session.get("cronologia_messaggi", [])
        storico_chat.append({"role": "user", "content": prompt_ingegnerizzato})

        # Inizializzazione del contenitore per lo streaming di testo sulla GUI di Chainlit
        messaggio_risposta_interattiva = cl.Message(content="")
        await messaggio_risposta_interattiva.send()

        # Chiamata asincrona nativa e streaming dei token progressivi
        async for token in AssistenteModelloLinguistico.esegui_flusso_chat(storico_chat):
            if token:
                await messaggio_risposta_interattiva.stream_token(str(token))

        # Salvataggio del messaggio finale dell'assistente nella cronologia di sessione
        storico_chat.append({"role": "assistant", "content": messaggio_risposta_interattiva.content})
        await messaggio_risposta_interattiva.update()
        cl.user_session.set("cronologia_messaggi", storico_chat)

    except Exception as eccezione_runtime:
        notifica_errore = f"Si è verificato un problema durante l'elaborazione: {str(eccezione_runtime)}"
        await cl.Message(content=notifica_errore).send()
        print(notifica_errore)
