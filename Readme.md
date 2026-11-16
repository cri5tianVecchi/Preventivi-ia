# Fase 0 — Listino demo materiale elettrico

Dati finti ma realistici: 262 articoli in 15 categorie, 16 regole di compatibilità e di business.
Le marche (Voltaria, Quadrix, Cavilux, Ferrotec, Plastex) e i codici sono inventati; i prezzi sono di listino, IVA esclusa e prima dello sconto.
I valori tecnici delle regole sono semplificati: non usarli per progettare impianti reali.

## File
- `schema.sql`: tabelle `articoli`, `regole`, `preventivi`, `righe_preventivo` (con pgvector)
- `seed.sql`: popola `articoli` e `regole`
- `listino.csv`: lo stesso listino, da aprire in Excel o da usare per testare l'import
- `regole.json`: le regole; ogni `tipo` diventa una funzione Python nel motore (Fase 1)
- `genera_listino.py`: rigenera CSV e seed (`python genera_listino.py .`, con `regole.json` nella stessa cartella)

## Avvio rapido
```bash
docker run -d --name preventivi-db -e POSTGRES_PASSWORD=dev -p 5432:5432 pgvector/pgvector:pg16
psql -h localhost -U postgres -f schema.sql
psql -h localhost -U postgres -f seed.sql
```