import os
from ollama import AsyncClient
from config import ImpostazioniSistema

client_ollama_locale = AsyncClient(host=ImpostazioniSistema.URL_ENDPOINT_API)

class AssistenteModelloLinguistico:

    @staticmethod
    async def genera_risposta_stream(cronologia_messaggi):
        """Invia lo storico della chat a Ollama abilitando lo streaming asincrono nativo."""
        try:
            flusso = await client_ollama_locale.chat(
                model=ImpostazioniSistema.MODELLO_CHAT, 
                messages=cronologia_messaggi, 
                stream=True
            )
            async for frammento in flusso:
                if frammento and 'message' in frammento and 'content' in frammento['message']:
                    yield frammento['message']['content']
        except Exception as e:
            yield f"\n❌ Errore durante la generazione dello streaming Ollama: {str(e)}"

    @staticmethod
    async def estrai_nominativo_candidato(estratto_anagrafica):
        if not estratto_anagrafica.strip():
            return "Profilo Estratto"
            
        prompt_estrazione = f"""
        Analizza le seguenti righe ed estrai esclusivamente il nome e il cognome della persona titolare del CV.
        Rispondi solo ed esclusivamente con il nome e cognome, senza punteggiatura, formule di cortesia o commenti.
        Testo da analizzare:
        {estratto_anagrafica}
        """
        try:
            risposta = await client_ollama_locale.chat(
                model=ImpostazioniSistema.MODELLO_CHAT,
                messages=[{"role": "user", "content": prompt_estrazione}]
            )
            nome = risposta['message']['content'].strip()
            return nome if "\n" not in nome else nome.split("\n")[0]
        except Exception:
            return "Candidato"

    @staticmethod
    async def ottieni_statistiche_db(informazioni_db):
        prompt_statistiche = f"""
        Formatta in modo elegante, leggibile e sintetico in lingua italiana le seguenti statistiche di indicizzazione del modulo HR:
        Nome Collezione: {informazioni_db.get('nome_collezione', 'Sconosciuta')}
        Frammenti totali a sistema: {informazioni_db.get('frammenti_totali', 0)}
        Numero Curricula unici elaborati: {informazioni_db.get('file_unici', 0)}
        
        Usa i punti elenco. Sii professionale.
        """
        try:
            risposta = await client_ollama_locale.chat(
                model=ImpostazioniSistema.MODELLO_CHAT,
                messages=[{"role": "user", "content": prompt_statistiche}]
            )
            return risposta['message']['content'].strip()
        except Exception as e:
            return f"Statistiche: {informazioni_db}"

    @staticmethod
    def genera_prompt_strutturato(testo_contesto, quesito_utente, nome_candidato):
        return f"""
        Agisci come un consulente HR senior ed esperto recruiter. Fornisci risposte mirate e professionali basate sul contesto fornito.
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
