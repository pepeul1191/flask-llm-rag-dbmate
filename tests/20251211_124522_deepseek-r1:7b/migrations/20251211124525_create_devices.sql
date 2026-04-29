-- migrate:up

CREATE TABLE devices (
    id INTEGER PRIMARY KEY,
    brand VARCHAR(30),
    type VARCHAR(30),
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- migrate:down

DROP TABLE IF EXISTS devices;