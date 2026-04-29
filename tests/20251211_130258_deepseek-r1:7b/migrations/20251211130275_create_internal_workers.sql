-- migrate:up

CREATE TABLE internal_workers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code INT
);

-- migrate:down

DROP TABLE IF EXISTS internal_workers;