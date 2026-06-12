import chainlit as cl

@cl.on_message
async def gestisci_messaggio_utente(message: cl.Message):
    testo_ricevuto = message.content
    risposta_eco = f"Ciao! Ho ricevuto il tuo messaggio: {testo_ricevuto}."
    await cl.Message(content=risposta_eco).send()
