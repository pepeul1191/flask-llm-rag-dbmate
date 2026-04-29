-- migrate:up

CREATE TABLE externals (
    id INT AUTO_INCREMENT PRIMARY KEY
);

-- migrate:down

DROP TABLE IF EXISTS externals;