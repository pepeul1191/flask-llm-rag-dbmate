-- migrate:up

Create table entities to create

CREATE TABLE document_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(22)
);

-- migrate:down

DROP TABLE IF EXISTS entities;