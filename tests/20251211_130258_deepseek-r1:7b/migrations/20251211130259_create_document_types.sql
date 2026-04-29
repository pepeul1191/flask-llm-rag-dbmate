-- migrate:up

CREATE TABLE document_types (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(22)
);

-- migrate:down

DROP TABLE IF EXISTS document_types;