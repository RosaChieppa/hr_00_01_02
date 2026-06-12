# Smart HR Assistant - Sistema RAG per l'Analisi dei CV

Questo progetto è un assistente virtuale basato sull'Intelligenza Artificiale progettato per supportare i team HR nella ricerca e selezione dei candidati. Utilizza un approccio RAG (Retrieval-Augmented Generation) per analizzare i curricula presenti nella cartella locale ed estrarre il profilo ideale in base alle richieste dell'utente.

## Caratteristiche Tecniche
- **Database Vettoriale**: ChromaDB per l'archiviazione e l'indicizzazione dei frammenti di testo.
- **Modello di Embedding**: OpenAI (`text-embedding-3-small`) per convertire i testi dei CV in vettori.
- **Modello Generativo**: Ollama con il modello locale `llama3.2` per elaborare le risposte in streaming.
- **Interfaccia Utente**: Chainlit per una chat interattiva e moderna.

## Struttura del Progetto
- `hr_assistant/__init__.py`: Punto di ingresso dell'applicazione e gestione degli eventi della chat.
- `resumes/`: Cartella contenente i curricula dei candidati in formato `.txt`.
- `pyproject.toml`: Configurazione del progetto e gestione delle dipendenze con Poetry.

## Requisiti e Installazione

Assicurati di avere configurato Poetry e installato Ollama con il modello `llama3.2`.

1. Installa le dipendenze del progetto:
```bash
poetry install
```

2. Attiva l'ambiente virtuale:
```bash
eval \$(poetry env activate)
```

## Esecuzione dell'Applicazione

Avvia l'interfaccia di Chainlit in modalità di ricarica automatica con il seguente comando:
```bash
poetry run chainlit run hr_assistant/__init__.py -w
```
