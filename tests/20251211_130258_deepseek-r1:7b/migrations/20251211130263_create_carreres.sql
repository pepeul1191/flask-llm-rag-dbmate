-- migrate:up

CREATE TABLE carreres (
    id INT AUTO_INCREMENT PRIMARY KEY
);

-- migrate:down

DROP TABLE IF EXISTS carreres;