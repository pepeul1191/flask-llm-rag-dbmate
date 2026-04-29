-- migrate:up

CREATE TABLE document_types(
    id INTEGER PRIMARY KEY AUTO_INCREMENT NOT NULL UNIQUE ,
     name VARCHAR (25)NOT  null,   -- ADD ALL COLUMNS HERE WITH ACTUAL DATA TYPES. Example : username VARCHAR(50), notnull constraint added here as per requirement and also unique constraints are set for id column to avoid duplicate entries in the table document_types
    created_at timestamp DEFAULT CURRENT_TIMESTAMP,  --DEFAULT values where appropriate  
);

-- migrate:down

DROP TABLE IF EXISTS;