-- migrate:up

INSERT INTO projects (id, title, description, engine_id, connection_string) VALUES
  (1, 'COA Concurso de Fotografía',
   'El sistema RAG en nuestra aplicación funciona como el motor inteligente que asiste al LLM a convertir diagramas PlantUML en código SQL mediante un proceso contextualizado.',
   1,
   'sqlite:///db/coa_concurso.sqlite');
INSERT INTO projects (id, title, description, engine_id, connection_string) VALUES
  (2, 'Innnova Rails',
   'La Aplicación Web recibe el diagrama PlantUML y parámetros del usuario, enviándolos al Operador de Embedding que genera representaciones vectoriales del modelo.',
   2,
   'mysql://user:password@localhost:3306/innova_rails');
INSERT INTO projects (id, title, description, engine_id, connection_string) VALUES
  (3, 'Quinua Smart',
   'El Constructor de Prompt integra entonces el PlantUML original con el contexto enriquecido obtenido, creando un prompt ampliado que se envía al LLM.',
   3,
   'postgres://user:password@localhost:5432/quinua_smart');


-- migrate:down

DELETE FROM projects;