-- migrate:up

CREATE TABLE internal_workers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code INT NOT NULL,
    participant_id INT,
    FOREIGN KEY (participant_id) REFERENCES participants(id)
);

-- migrate:down

DROP TABLE IF EXISTS internal_workers;