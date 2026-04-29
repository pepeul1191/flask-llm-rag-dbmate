-- migrate:up

CREATE TABLE internals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code INT
);

-- migrate:down

DROP TABLE IF EXISTS internals;