-- migrate:up

CREATE TABLE specialisms_count (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    specialism_id INTEGER NOT NULL,
    count INTEGER NOT NULL,
    FOREIGN KEY (specialism_id) REFERENCES specialisms(id)
);

-- migrate:down

DROP TABLE specialisms_count;