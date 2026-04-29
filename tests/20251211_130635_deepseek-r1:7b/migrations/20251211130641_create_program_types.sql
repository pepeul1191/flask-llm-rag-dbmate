-- migrate:up

CREATE TABLE program_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(30),
    description TEXT,
    image_url VARCHAR(60),
    pdf_url VARCHAR(60),
    max_participant_team INT,
    created_at DATETIME,
    updated_at DATETIME
);

-- migrate:down

DROP TABLE IF EXISTS program_types;