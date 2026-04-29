-- migrate:up

CREATE TABLE permissions ( id INTEGER PRIMARY KEY AUTO_INCREMENT, name VARCHAR(40), created DATETIME, updated DATETIME, role_id INTEGER, FOREIGN KEY (role_id) REFERENCES roles(id) );

-- migrate:down

DROP TABLE IF EXISTS PERMISSIONS;