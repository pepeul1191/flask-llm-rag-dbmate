-- migrate:up

CREATE TABLE mentors_specialisms (
    mentor_id INT,
    specialism_id INT,
    PRIMARY KEY (mentor_id, specialism_id),
    FOREIGN KEY (mentor_id) REFERENCES mentors(id),
    FOREIGN KEY (specialism_id) REFERENCES specialisms(id)
);

-- migrate:down

DROP TABLE IF EXISTS mentors_specialisms;