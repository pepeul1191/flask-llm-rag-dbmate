-- migrate:up

CREATE TABLE mentors_spcialisms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mentor_id INTEGER,
    specialization_id INTEGER,
    FOREIGN KEY (mentor_id) REFERENCES mentors(id),
    FOREIGN KEY (specialization_id) REFERENCES specialisms(id)
);

-- migrate:down

DROP TABLE IF EXISTS mentors_spcialisms;