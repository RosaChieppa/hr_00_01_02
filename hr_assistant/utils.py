import os
from ollama import AsyncClient
from config import ImpostazioniSistema

client_ollama_locale = AsyncClient(host=ImpostazioniSistema.URL_ENDPOINT_API)

class AssistenteModelloLinguistico:

    @staticmethod
    async def esegui_flusso_chat(cronologia_messaggi):
        """Invia lo storico della chat a Ollama abilitando lo streaming nativo."""
        flusso = await client_ollama_locale.chat(
            model=ImpostazioniSistema.MODELLO_CHAT, 
            messages=cronologia_messaggi, 
            stream=True
        )
        async for frammento in flusso:
            if frammento and 'message' in frammento and 'content' in frammento['message']:
                yield frammento['message']['content']

    @staticmethod
    async def genera_risposta_stream(cronologia_messaggi):
        async for frammento in AssistenteModelloLinguistico.esegui_flusso_chat(cronologia_messaggi):
            yield frammento

    @staticmethod
    async def estrai_nominativo_candidato(estratto_anagrafica):
        """Isola il nome e il cognome del candidato dalle prime righe del testo."""
        if not estratto_anagrafica.strip():
            return "Profilo Estratto"
            
        prompt_estrazione = f"""
        Analizza le seguenti righe iniziali di un CV ed estrai esclusivamente il nome e il cognome della persona. 
        Rispondi solo con il nome e cognome, senza aggiungere nient'altro: 
        {estratto_anagrafica}
        """
        try:
            risposta = await client_ollama_locale.chat(
                model=ImpostazioniSistema.MODELLO_CHAT,
                messages=[{"role": "user", "content": prompt_estrazione}]
            )
            return risposta['message']['content'].strip()
        except Exception:
            return "Candidato"

    @staticmethod
    async def ottieni_statistiche_db(informazioni_db):
        prompt_statistiche = f"""
        Descrivi in modo testuale e sintetico in italiano queste statistiche di indicizzazione: {informazioni_db}
        """
        risposta = await client_ollama_locale.chat(
            model=ImpostazioniSistema.MODELLO_CHAT,
            messages=[{"role": "user", "content": prompt_statistiche}]
        )
        return risposta['message']['content'].strip()

    @staticmethod
    def genera_prompt_strutturato(testo_contesto, quesito_utente, nome_candidato):
        """Sviluppa il prompt strutturato inserendo i vincoli aziendali HR."""
        return f"""
        Agisci come un consulente HR senior. Fornisci risposte mirate e professionali basate sul contesto fornito.
        DEVI RISPONDERE TASSATIVAMENTE IN LINGUA ITALIANA.

        CONTESTO ESTRATTO DAL CV:
        [[[
        {testo_contesto}
        ]]].
        
        DOMANDA DELL'UTENTE: [[[ {quesito_utente} ]]].
        
        Linee guida tassative per la generazione della risposta:
        1. Spiega in modo chiaro se nel profilo analizzato ci sono le competenze adatte richieste dall'utente.
        2. Argomenta la risposta in modo solido utilizzando esclusivamente le informazioni presenti nel contesto sopra riportato.
        3. Se non trovi informazioni utili nel documento, dichiara l'impossibilità di rispondere senza inventare nulla.
        4. Alla fine della risposta, crea una sezione intitolata "CONTATTI CANDIDATO" indicando il nome ([[[ {nome_candidato} ]]]), email e telefono se visibili nel contesto.
        """
