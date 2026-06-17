## 03

- Sync Documenti automatico all'avvio dell'applicazione.

## 04

- Inserimento tasti interattivi nell'interfaccia Chainlit: `db_info` (Statistiche) e `db_reindex` (Reindicizzazione).

## 05

- Integrazione della logica di Semantic Chunking per una segmentazione intelligente dei testi basata sul contesto.

## 06

- Refactoring completo del modulo Semantic Chunking per ottimizzare le prestazioni di frammentazione.

## 07

- Implementazione della lettura e dell'estrazione del testo da file di formato diverso (PDF, Word, Excel, HTML e archivi ZIP).
- Libreria utilizzata per la conversione universale: `microsoft/markitdown`.
- Installazione delle dipendenze binarie necessarie per l'elaborazione dei documenti tramite: `poetry add markitdown` o `pip install "markitdown[pdf]"`.
- Ottimizzazione del Semantic Chunking con l'aggiunta della funzione interna `_split_into_sentences` per evitare che un file generi frammenti o frasi singole isolate.

## 08 - Upload file da interfaccia

- Possibilità di aggiungere uno o più file (curricula) nella cartella `resumes` direttamente dall'interfaccia di Chainlit tramite Drag & Drop o icona della graffetta.
- Introduzione della sanificazione automatica dei nomi dei file in ingresso (sostituzione degli spazi con caratteri di sottolineatura `_` e rimozione di punti consecutivi) per bypassare i blocchi nativi dei server web ("Upload failed").
- Gestione sicura del flusso di copia dei file binari dal percorso temporaneo di sessione alla cartella locale definitiva tramite la libreria `shutil.copy` (risolto l'errore `TypeError: NoneType`).
- Aggiornamento istantaneo e automatico del database vettoriale degli embedding (`ChromaDB`) subito dopo il caricamento di un nuovo documento.
- Creazione di una nuova azione interattiva a schermo (`Azzera DB`) per svuotare, eliminare e reinizializzare la collezione vettoriale da zero con un singolo clic.
- Corretto il parsing delle risposte estratted da ChromaDB in `app.py` gestendo in modo robusto le liste di liste annidate (`risultati_ricerca["metadatas"][0]`).
