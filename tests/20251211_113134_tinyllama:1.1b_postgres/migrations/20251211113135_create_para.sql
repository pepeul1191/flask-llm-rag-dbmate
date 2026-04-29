-- migrate:up

CREATE TABLE para PostgreSQL con formato EXACTO.
3. Usa el formato exacto de migración para cada tabla.

REQUISITOS TÉCNICOS:

- Para PostgreSQL, usa tipos de datos apropiados (INTEGER, VARCHAR, DATE, BOOLEAN).
- Incluye PRIMARY KEY autoincremental para cada tabla.
- Incluye FOREIGN KEYS basadas en las relaciones del diagrama.
- Mantén los nombres originales en inglés.

Generar código SQL:

```sql
-- migrate:up

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(20) NOT NULL,
  password VARCHAR(100) NOT NULL,
  activation_key VARCHAR(30) NOT NULL,
  reset_key VARCHAR(30) NOT NULL,
  email VARCHAR(50),
  activated BOOLEAN NOT NULL DEFAULT TRUE,
  created DATE NOT NULL DEFAULT CURRENT_DATE,
  updated DATE NOT NULL DEFAULT CURRENT_DATE
);

-- migrate:down

DROP TABLE IF EXISTS para;