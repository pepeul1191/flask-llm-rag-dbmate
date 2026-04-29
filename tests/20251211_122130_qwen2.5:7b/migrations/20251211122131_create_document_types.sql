-- migrate:up

CREATE TABLE document_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(22) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS document_types;