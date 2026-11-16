# Richieste d'offerta di prova

Documenti finti (clienti e nomi inventati) per testare estrazione e matching.
Per ogni documento, `atteso/<nome>.json` contiene le righe corrette (codice del listino e quantità) e gli avvisi che il motore regole deve generare. Lo script di valutazione della Fase 3 confronta l'output dell'IA con questi file.

| Documento | Difficoltà | Righe | Avvisi attesi |
|---|---|---|---|
| `rfq_01_elenco_pulito.pdf` | facile | 14 | R05 |
| `rfq_02_email_disordinata.pdf` | difficile | 12 | R08, R10, R15 |
| `rfq_03_distinta_excel.xlsx` | media | 11 | R04, R15 |
| `rfq_04_scansione.pdf` | difficile | 5 | R01, R10, R15 |
| `rfq_05_capitolato.pdf` | difficile | 8 | R15 |

Regole per la valutazione:
- `codice_atteso: null` → la riga NON deve essere abbinata a nessun articolo.
- `alternative_accettabili` → anche questi codici contano come corretti.
