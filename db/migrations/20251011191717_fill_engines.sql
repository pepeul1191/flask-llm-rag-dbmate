-- migrate:up

INSERT INTO engines (id, name, image) VALUES (1, 'SQLite3', '/img/sqlite.png');
INSERT INTO engines (id, name, image) VALUES (2, 'MySQL', '/img/mysql.png');
INSERT INTO engines (id, name, image) VALUES (3, 'Postgres', '/img/postgres.png');

-- migrate:down

DELETE FROM engines;