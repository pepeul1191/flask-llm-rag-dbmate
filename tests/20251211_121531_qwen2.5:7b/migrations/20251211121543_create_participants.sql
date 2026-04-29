-- migrate:up

CREATE TABLE participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    names VARCHAR(50),
    last_names VARCHAR(50),
    email VARCHAR(40),
    phone VARCHAR(40),
    dni VARCHAR(20),
    created_at DATETIME,
    updated_at DATETIME,
    dni_type_id INTEGER,
    nation_id INTEGER,
    user_id INTEGER,
    FOREIGN KEY (dni_type_id) REFERENCES dni_types(id),
    FOREIGN KEY (nation_id) REFERENCES nations(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- migrate:down

DROP TABLE IF EXISTS participants;