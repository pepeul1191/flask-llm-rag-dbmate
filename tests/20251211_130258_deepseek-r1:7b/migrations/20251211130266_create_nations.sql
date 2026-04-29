-- migrate:up

CREATE TABLE nations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(30)
);

-- migrate:down

DROP TABLE IF EXISTS nations;