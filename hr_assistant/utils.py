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

    @staticmethod
    def genera_prompt_strutturato(testo_contesto, quesito_utente, nome_candidato):
        """Sviluppa il prompt finale inserendo i vincoli di risposta per il modello locale."""
        return f"""
            Scenario documentale di riferimento:
            [[[
            {testo_contesto}
            ]]].
            Richiesta formulata dall'utente: [[[ {quesito_utente} ]]] .
            Linee guidelines tassative per la generazione della risposta:
            1. Specifica chiaramente che nel file identificato risiede il profilo professionale ottimale.
            2. Ricordati di esplicitare chiaramente il nome del file all'interno della risposta.
            3. Assicurati di includere espressamente il nome del candidato: [[[ {nome_candidato} ]]].
            4. Sviluppa un'argomentazione solida basando le tue motivazioni solo sulle competenze estratte dal contesto sopra riportato.
            5. Qualora non si riscontrasse alcuna affinità semantica o informazione utile nei documenti, dichiara l'impossibilità di rispondere senza inventare dati non presenti."""
