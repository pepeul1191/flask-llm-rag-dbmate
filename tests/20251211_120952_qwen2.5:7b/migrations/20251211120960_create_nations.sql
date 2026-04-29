-- migrate:up

CREATE TABLE nations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(30) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS nations;