-- migrate:up

CREATE TABLE programs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(30),
    description TEXT,
    image_url VARCHAR(60),
    pdf_url VARCHAR(60),
    max_participant_team INT,
    created_at DATETIME,
    updated_at DATETIME,
    created_by VARCHAR(255)
);

-- migrate:down

DROP TABLE IF EXISTS programs;