-- migrate:up

CREATE TABLE tableName(id INTEGER PRIMARY KEY AUTO_INCREMENT NOT NULL UNIQUE , name VARCHAR (50)NOT  null, created_at timestamp DEFAULT CURRENT_TIMESTAMP);

-- migrate:down

DROP TABLE IF EXISTS tableName;