-- migrate:up

CREATE TABLE programs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(30) NOT NULL,
    description TEXT,
    image_url VARCHAR(60),
    pdf_url VARCHAR(60),
    max_participant_team INT,
    created_at DATETIME,
    updated_at DATETIME,
    program_type_id INT,
    period_id INT,
    FOREIGN KEY (program_type_id) REFERENCES program_types(id),
    FOREIGN KEY (period_id) REFERENCES periods(id)
);

-- migrate:down

DROP TABLE IF EXISTS programs;