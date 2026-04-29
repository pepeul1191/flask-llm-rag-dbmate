-- migrate:up

CREATE TABLE devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand VARCHAR(30) NOT NULL,
    type VARCHAR(30) NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- migrate:down

DROP TABLE devices;