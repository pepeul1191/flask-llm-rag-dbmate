-- migrate:up

CREATE TABLE systems_users ( id INTEGER PRIMARY KEY AUTO_INCREMENT, system_id INTEGER, user_id INTEGER, created DATETIME, FOREIGN KEY (system_id) REFERENCES systems(id), FOREIGN KEY (user_id) REFERENCES users(id) );

-- migrate:down

DROP TABLE IF EXISTS SYSTEMS_USERS;