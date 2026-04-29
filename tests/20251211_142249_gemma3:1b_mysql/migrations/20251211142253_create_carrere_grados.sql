-- migrate:up

CREATE TABLE carrere_grados (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(40)
);

-- migrate:down

DROP TABLE carrere_grados;