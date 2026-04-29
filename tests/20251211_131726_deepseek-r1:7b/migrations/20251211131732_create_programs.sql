-- migrate:up

CREATE TABLE programs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(30),
    description TEXT,
    image_url VARCHAR(60),
    pdf_url VARCHAR(60),
    max_participant_team INT,
    created_at DATE,
    updated_at DATE
);

-- migrate:down

DROP TABLE IF EXISTS programs;