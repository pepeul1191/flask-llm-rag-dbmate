-- migrate:up

CREATE TABLE` statements for the specified entities, you can use the following code:

```sql
-- Create the 'users' table
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  username VARCHAR(30)
);

-- migrate:down

DROP TABLE IF EXISTS users;