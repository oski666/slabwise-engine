# Istruzioni per Claude

1. Prima di qualsiasi lavoro leggi `docs/PILLARS.md` e seguilo alla lettera; per sapere a che punto è il lavoro leggi `docs/STATUS.md` (aggiornalo quando chiudi un lavoro importante). Se una richiesta contraddice un pilastro, dillo prima di agire.
2. Un pilastro, il metodo o il perimetro si cambiano solo così: prima la voce datata in `docs/DECISIONS.md`, poi il documento, poi il codice.
3. Ogni modifica al metodo passa dal backtest (`docs/BACKTEST_PROTOCOL.md`). Le soglie non si cambiano dopo aver visto i risultati; un nuovo criterio si registra prima.
4. `docs/METHOD.md` descrive esattamente il codice: se divergono, correggi il codice o aggiorna il documento nella stessa modifica.
5. Prima di ogni commit: `python -m pytest -q tests`.
6. Mai presentare risultati del mercato simulato come risultati reali (P14).
7. Fonti di dati: ognuna registrata in `docs/DATA_SOURCES.md` con provenienza e rischi (P18 rimosso, D26); nessuna spesa senza decisione nel registro (P19).
8. Il proprietario del progetto è Oscar: comunica in italiano.
