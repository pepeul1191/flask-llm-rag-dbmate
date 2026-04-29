-- migrate:up

CREATE TABLE mentors_specialisms (
    id SERIAL PRIMARY KEY,
    mentor_id INTEGER REFERENCES mentors(id),
    specialism_id INTEGER REFERENCES specialisms(id)
);

-- migrate:down

DROP TABLE IF EXISTS mentors_specialisms;