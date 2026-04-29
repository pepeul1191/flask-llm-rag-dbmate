-- migrate:up

CREATE TABLE program_types (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(30) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS program_types;