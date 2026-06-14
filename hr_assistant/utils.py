# utils.py
from ollama import AsyncClient
from hr_assistant.config import ImpostazioniSistema

# Inizializziamo il client asincrono di Ollama collegandolo all'indirizzo di configurazione
client_ollama_locale = AsyncClient(host=ImpostazioniSistema.URL_ENDPOINT_API)

class AssistenteModelloLinguistico:

    @staticmethod
    async def esegui_flusso_chat(cronologia_messaggi):
        """Invia lo storico della chat a Ollama abilitando lo streaming nativo in modo asincrono."""
        flusso = await client_ollama_locale.chat(
            model=ImpostazioniSistema.MODELLO_CHAT, 
            messages=cronologia_messaggi, 
            stream=True
        )
        
        # Iterazione asincrona sui token inviati da Ollama
        async for frammento in flusso:
            yield frammento['message']['content']

    @staticmethod
    async def estrai_nominativo_candidato(estratto_anagrafica):
        """Analizza l'intestazione del file per isolare l'anagrafica in modo asincrono."""
        prompt_estrazione = f"""
        Analizza le seguenti righe iniziali del curriculum vitae ed estrai esclusivamente il nome e il cognome del candidato. 
        Rispondi solo ed esclusivamente con il nome e cognome, senza aggiungere alcun commento aggiuntivo o prefisso: 
        {estratto_anagrafica}
        """
        
        risposta_modello = await client_ollama_locale.chat(
            model=ImpostazioniSistema.MODELLO_CHAT,
            messages=[
                {
                    "role": "user",
                    "content": prompt_estrazione,
                }
            ]
        )
        
        return risposta_modello['message']['content'].strip()

    # --- NUOVA INTEGRAZIONE: GENERAZIONE DELLE STATISTICHE DB TRAMITE LLM ---
    @staticmethod
    async def ottieni_statistiche_db(informazioni_db):
        """Descrive in modo testuale e sintetico le statistiche legate al database vettoriale locale."""
        prompt_statistiche = f"""
        Il tuo compito è quello di descrivere in modo testuale, ma sintetico, le statistiche legate al database dei frammenti indicizzati da questo sistema. 
        Dammi pure la percentuale di frammenti indicizzati rispetto al totale dei file presenti nel database. 
        Ecco le informazioni necessarie per le statistiche da fornire: {informazioni_db}
        """
        
        risposta_modello = await client_ollama_locale.chat(
            model=ImpostazioniSistema.MODELLO_CHAT,
            messages=[
                {
                    "role": "user",
                    "content": prompt_statistiche,
                }
            ]
        )
        
        return risposta_modello['message']['content'].strip()
    # --- FINE NUOVA INTEGRAZIONE ---

    @staticmethod
    def genera_prompt_strutturato(testo_contesto, quesito_utente, nome_candidato):
        """Sviluppa il prompt finale inserendo i vincoli di risposta per il modello locale."""
        # INTEGRAZIONE LOGICA SORGENTE: Aggiornati i vincoli sul posizionamento del nome del file e la sezione contatti
        return f"""
            Dato il seguente contesto:
            [[[
            {testo_contesto}
            ]]].
            Rispondi alla domanda dell'utente: [[[ {quesito_utente} ]]].
            
            Linee guida tassative per la generazione della risposta:
            1. Spiega in modo chiaro che nel file individuato c'è il profilo più adatto alle richieste dell'utente.
            2. Argomenta la scelta in modo solido utilizzando esclusivamente il contenuto del testo individuato nel contesto sopra riportato.
            3. Qualora non si riscontrasse alcuna affinità semantica o informazione utile nei documenti, dichiara l'impossibilità di rispondere senza inventare dati.
            4. Alla fine della risposta, crea una sezione dedicata esplicitamente ai contatti del candidato indicando il nome ([[[ {nome_candidato} ]]]), la sua email e il numero di telefono.
            5. Subito dopo la sezione dei contatti indica il Nome del file del CV di origine. Non menzionare o nominare mai il nome del file prima di questa specifica sezione conclusiva.
        """
