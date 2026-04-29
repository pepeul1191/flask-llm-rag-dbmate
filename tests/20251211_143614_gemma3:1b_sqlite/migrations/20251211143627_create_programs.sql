-- migrate:up

CREATE TABLE programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(30) NOT NULL,
    description TEXT,
    image_url VARCHAR(60),
    pdf_url VARCHAR(60),
    max_participant_team INTEGER,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- migrate:down

DROP TABLE programs;