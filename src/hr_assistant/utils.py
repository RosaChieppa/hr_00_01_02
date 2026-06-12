# utils.py
from openai import OpenAI
from hr_assistant.config import ImpostazioniSistema

# Client centralizzato basato sulle configurazioni del nostro progetto
client_openai_servizio = OpenAI(
    base_url=ImpostazioniSistema.URL_ENDPOINT_API, 
    api_key=ImpostazioniSistema.CHIAVE_OPENAI_CHAT
)


class AssistenteModelloLinguistico:

    @staticmethod
    def esegui_flusso_chat(cronologia_messaggi):
        """Invia lo storico della chat al modello LLM abilitando lo streaming della risposta."""
        return client_openai_servizio.chat.completions.create(
            model=ImpostazioniSistema.MODELLO_CHAT, 
            messages=cronologia_messaggi, 
            stream=True
        )

    @staticmethod
    async def estrai_nominativo_candidato(estratto_anagrafica):
        """Analizza l'intestazione del file per isolare unicamente l'anagrafica del profilo."""
        risposta_modello = client_openai_servizio.chat.completions.create(
            model=ImpostazioniSistema.MODELLO_CHAT,
            messages=[
                {
                    "role": "user",
                    "content": f"""
                      Analizza le seguenti righe iniziali del curriculum vitae ed estrai esclusivamente il nome e il cognome del candidato. Rispondi solo ed esclusivamente con il nome e cognome, senza aggiungere alcun commento aggiuntivo o prefisso: {estratto_anagrafica}
                      """,
                }
            ],
        )
        return risposta_modello.choices[0].message.content.strip()

    @staticmethod
    def genera_prompt_strutturato(testo_contesto, quesito_utente, nome_candidato):
        """Sviluppa il prompt finale inserendo i vincoli di risposta per il modello generativo."""
        return f"""
            Scenario documentale di riferimento:
            [[[
            {testo_contesto}
            ]]].
            Richiesta formulata dall'utente: [[[ {quesito_utente} ]]] .
            Linee guida tassative per la generazione della risposta:
            1. Specifica chiaramente che nel file identificato risiede il profilo professionale ottimale.
            2. Ricordati di esplicitare chiaramente il nome del file all'interno della risposta.
            3. Assicurati di includere espressamente il nome del candidato: [[[ {nome_candidato} ]]].
            4. Sviluppa un'argomentazione solida basando le tue motivazioni solo sulle competenze estratte dal contesto sopra riportato.
            5. Qualora non si riscontrasse alcuna affinità semantica o informazione utile nei documenti, dichiara l'impossibilità di rispondere senza inventare dati non presenti."""