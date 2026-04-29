-- migrate:up

CREATE TABLE industries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(30) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS industries;