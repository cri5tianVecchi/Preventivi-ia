-- Schema database — Fase 0/1
-- PostgreSQL 15+ con estensione pgvector

CREATE EXTENSION IF NOT EXISTS vector;

-- Listino articoli
CREATE TABLE articoli (
    id              SERIAL PRIMARY KEY,
    codice          TEXT NOT NULL UNIQUE,
    descrizione     TEXT NOT NULL,
    categoria       TEXT NOT NULL,
    marca           TEXT NOT NULL,
    unita           TEXT NOT NULL CHECK (unita IN ('pz', 'm')),
    confezione      INTEGER NOT NULL DEFAULT 1 CHECK (confezione > 0),   -- multiplo minimo di vendita
    prezzo_listino  NUMERIC(10,2) NOT NULL CHECK (prezzo_listino >= 0),  -- euro, IVA esclusa, prima dello sconto
    moduli_din      INTEGER,                                             -- NULL se non è un dispositivo modulare
    attributi       JSONB NOT NULL DEFAULT '{}'::jsonb,                  -- specifiche tecniche
    attivo          BOOLEAN NOT NULL DEFAULT TRUE,
    -- Embedding della descrizione per il matching (Fase 3).
    -- Adatta la dimensione al modello di embedding che sceglierai.
    embedding       vector(1024),
    aggiornato_il   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_articoli_categoria ON articoli (categoria);
CREATE INDEX idx_articoli_attributi ON articoli USING GIN (attributi);
-- Da creare dopo aver popolato gli embedding:
-- CREATE INDEX idx_articoli_embedding ON articoli USING hnsw (embedding vector_cosine_ops);

-- Regole di compatibilità e di business
CREATE TABLE regole (
    id           TEXT PRIMARY KEY,                      -- es. 'R01'
    nome         TEXT NOT NULL,
    gravita      TEXT NOT NULL CHECK (gravita IN ('blocco', 'avviso')),
    tipo         TEXT NOT NULL,                         -- nome della funzione che la valuta
    descrizione  TEXT NOT NULL,
    parametri    JSONB NOT NULL DEFAULT '{}'::jsonb,
    attiva       BOOLEAN NOT NULL DEFAULT TRUE
);

-- Preventivi
CREATE TABLE preventivi (
    id                  SERIAL PRIMARY KEY,
    numero              TEXT UNIQUE,                    -- es. '2026-0001'
    cliente             TEXT,
    stato               TEXT NOT NULL DEFAULT 'bozza'
                        CHECK (stato IN ('in_elaborazione', 'bozza', 'revisionato', 'inviato', 'accettato', 'rifiutato')),
    documento_origine   TEXT,                           -- percorso/URL del file caricato
    contesto            JSONB NOT NULL DEFAULT '{}'::jsonb,  -- es. {"ambiente": "esterno", "icc_presunta_ka": 6}
    note                TEXT,
    creato_il           TIMESTAMPTZ NOT NULL DEFAULT now(),
    aggiornato_il       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Righe del preventivo
CREATE TABLE righe_preventivo (
    id                     SERIAL PRIMARY KEY,
    preventivo_id          INTEGER NOT NULL REFERENCES preventivi(id) ON DELETE CASCADE,
    ordine                 INTEGER NOT NULL,
    articolo_id            INTEGER REFERENCES articoli(id),   -- NULL se non ancora abbinato
    descrizione_originale  TEXT,                              -- testo estratto dal documento
    quantita_richiesta     NUMERIC(12,2) NOT NULL CHECK (quantita_richiesta > 0),
    quantita_fatturata     NUMERIC(12,2),                     -- dopo arrotondamento alla confezione
    prezzo_unitario        NUMERIC(10,2),                     -- copiato dal listino al momento del calcolo
    sconto_pct             NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (sconto_pct BETWEEN 0 AND 100),
    gruppo                 TEXT,                              -- es. 'Quadro Q1': per le regole su quadri e linee
    circuito               JSONB NOT NULL DEFAULT '{}'::jsonb,-- es. {"tipo": "prese", "carico": "lavatrice"}
    confidenza_match       NUMERIC(4,3),                      -- 0..1, dal matching IA
    candidati              JSONB,                             -- alternative proposte dall'IA
    UNIQUE (preventivo_id, ordine)
);

CREATE INDEX idx_righe_preventivo ON righe_preventivo (preventivo_id);