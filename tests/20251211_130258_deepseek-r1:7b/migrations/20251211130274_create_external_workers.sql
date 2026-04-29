-- migrate:up

CREATE TABLE external_workers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    worker_id INT
);

-- migrate:down

DROP TABLE IF EXISTS external_workers;