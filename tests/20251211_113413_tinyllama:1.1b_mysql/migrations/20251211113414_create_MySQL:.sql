-- migrate:up

CREATE TABLE MySQL:
```sql
CREATE TABLE users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(30) NOT NULL,
  password VARCHAR(40) NOT NULL,
  first_names VARCHAR(50) NOT NULL,
  last_names VARCHAR(50) NOT NULL,
  email VARCHAR(30) NOT NULL,
  birth_date DATE NOT NULL,
  profile_picture VARCHAR(100) NOT NULL,
  sex BOOLEAN NOT NULL,
  reset_key VARCHAR(30) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS MySQL:;