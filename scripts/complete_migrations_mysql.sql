Aquí te presento los bloques de migración SQL para MYSQL correspondientes a cada tabla del diagrama UML:

**users**

-- migrate:up

CREATE TABLE users (
  id INT AUTO_INCREMENT,
  username VARCHAR(20) NOT NULL,
  password VARCHAR(100) NOT NULL,
  activation_key VARCHAR(30),
  reset_key VARCHAR(30),
  email VARCHAR(50) UNIQUE,
  activated BOOLEAN DEFAULT FALSE,
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
);

-- migrate:down

DROP TABLE users;

**systems**

-- migrate:up

CREATE TABLE systems (
  id INT AUTO_INCREMENT,
  name VARCHAR(40) NOT NULL,
  description TEXT,
  repository VARCHAR(100),
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
);

-- migrate:down

DROP TABLE systems;

**roles**

-- migrate:up

CREATE TABLE roles (
  id INT AUTO_INCREMENT,
  name VARCHAR(40) NOT NULL,
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  system_id INT,
  PRIMARY KEY (id),
  FOREIGN KEY (system_id) REFERENCES systems(id)
);

-- migrate:down

DROP TABLE roles;

**permissions**

-- migrate:up

CREATE TABLE permissions (
  id INT AUTO_INCREMENT,
  name VARCHAR(40) NOT NULL,
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  role_id INT,
  PRIMARY KEY (id),
  FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- migrate:down

DROP TABLE permissions;

**systems_users**

-- migrate:up

CREATE TABLE systems_users (
  id INT AUTO_INCREMENT,
  system_id INT NOT NULL,
  user_id INT NOT NULL,
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  FOREIGN KEY (system_id) REFERENCES systems(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- migrate:down

DROP TABLE systems_users;

**systems_users_permissions**

-- migrate:up

CREATE TABLE systems_users_permissions (
  id INT AUTO_INCREMENT,
  system_id INT NOT NULL,
  user_id INT NOT NULL,
  permission_id INT NOT NULL,
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  FOREIGN KEY (system_id) REFERENCES systems(id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (permission_id) REFERENCES permissions(id)
);

-- migrate:down

DROP TABLE systems_users_permissions;