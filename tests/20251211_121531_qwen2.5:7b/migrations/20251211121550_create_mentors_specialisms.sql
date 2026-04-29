-- migrate:up

CREATE TABLE mentors_specialisms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mentor_id INTEGER,
    specialism_id INTEGER,
    FOREIGN KEY (mentor_id) REFERENCES mentors(id),
    FOREIGN KEY (specialism_id) REFERENCES specialisms(id)
);

-- migrate:down

DROP TABLE IF EXISTS mentors_specialisms;