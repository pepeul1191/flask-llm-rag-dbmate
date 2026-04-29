-- migrate:up

CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(22) NOT NULL,
    chunk_type VARCHAR(30) NOT NULL,
    source_file_hash INTEGER NOT NULL,
    source_file VARCHAR(100) NOT NULL
);

-- migrate:down

DROP TABLE documents;