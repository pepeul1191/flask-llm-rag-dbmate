-- migrate:up

CREATE TABLE phases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(30),
    description TEXT,
    init_date DATE,
    end_date DATE,
    delivery_deadline DATE,
    evaluation_deadline DATE,
    revaluation_deadline DATE,
    created_at DATETIME,
    updated_at DATETIME
);

-- migrate:down

DROP TABLE IF EXISTS phases;