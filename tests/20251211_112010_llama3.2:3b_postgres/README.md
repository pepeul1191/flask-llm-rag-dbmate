# Migraciones SQL - biblio

**Fecha de generación:** 2025-12-11 11:20:10
**Tipo de base de datos:** postgres
**Archivo PUML origen:** biblio.puml
**Total de tablas generadas:** 10

## Estructura de carpetas

- `migrations/` - Archivos individuales de migración
- `complete_migrations_*.sql` - Todas las migraciones en un archivo
- `metadata.json` - Información de generación
- `README.md` - Este archivo

## Tablas generadas

1. `countries`
2. `users`
3. `books`
4. `authors`
5. `reviews`
6. `books_genres`
9. `devices`
11. `publishers`
13. `genres`
15. `books_authors`


### RESULTADOS

(venv) pepe@pepe-30fns02m00:~/Documents/UNMSM/2025-2/Semanario de Tesis 3/herramienta/tests/20251211_112010_llama3.2:3b_postgres$ python3 test.py

======================================================================
🔍 DIAGNÓSTICO Y EVALUACIÓN DEL SISTEMA RAG
======================================================================

💾 Total de chunks en ChromaDB: 25

──────────────────────────────────────────────────────────────────────
🔄 EVALUANDO CON K=5
──────────────────────────────────────────────────────────────────────

======================================================================
📊 EVALUANDO SISTEMA RAG (K=5)
======================================================================

📝 ✅ Tabla users
   Query: CREATE TABLE users con id INT PRIMARY KEY, username VARCHAR, password VARCHAR, e...
   ✅ OK: AP=1.000, Precision@5=1.000

📝 ✅ Tabla books
   Query: CREATE TABLE books con id, title VARCHAR, isbn VARCHAR, pages INT...
   ✅ OK: AP=1.000, Precision@5=1.000

📝 ✅ Tabla genres
   Query: CREATE TABLE genres con id INT, name VARCHAR...
   ✅ OK: AP=1.000, Precision@5=1.000

📝 ✅ Relación books-genres
   Query: CREATE TABLE books_genres con book_id INT, genre_id INT, FOREIGN KEY...
   ✅ OK: AP=1.000, Precision@5=0.800

📝 ✅ Tabla books_authors
   Query: CREATE TABLE books_authors con book_id INT, author_id INT...
   ✅ OK: AP=1.000, Precision@5=1.000

📝 ✅ Múltiples tablas
   Query: CREATE TABLE books, CREATE TABLE authors, CREATE TABLE books_authors con book_id...
   ✅ OK: AP=1.000, Precision@5=1.000

📝 ✅ Tabla reviews
   Query: CREATE TABLE reviews con rating INT, comment TEXT, review_date DATETIME, FOREIGN...
   ✅ OK: AP=1.000, Precision@5=0.400

📝 ❌ Tabla inexistente
   Query: CREATE TABLE inventory con stock INT, location VARCHAR...
   ✅ OK: AP=0.000, Precision@5=0.000

📝 ❌ Tabla shopping_cart
   Query: CREATE TABLE shopping_cart con user_id INT, product_id INT...
   ✅ OK: AP=0.000, Precision@5=0.000

📝 ⚠️ Query ambigua
   Query: tabla para guardar información de personas que usan el sistema con email y contr...
   ✅ OK: AP=1.000, Precision@5=1.000


======================================================================
📈 REPORTE DETALLADO (K=5)
======================================================================

🎯 MÉTRICAS GLOBALES:
   Mean Average Precision (MAP): 0.8000
   Mean Precision@5: 0.7200
   Mean Recall@5: 1.0000
   Mean NDCG@5: 0.8000
   Mean F1-Score: 0.7460
   MRR: 0.8000
   Expectation Rate: 100.00%

📊 POR TIPO DE QUERY:
   Positivas (8):
     - MAP: 1.0000
     - Precision@5: 0.9000
     - Recall@5: 1.0000

   Negativas (2):
     - False Positives: 0
     - Specificity: 100.00%

🎯 HIT RATES:
   Hit Rate@1: 80.00%
   Hit Rate@3: 80.00%
   Hit Rate@5: 80.00%

⚠️ QUERIES PROBLEMÁTICAS:

──────────────────────────────────────────────────────────────────────
🔄 EVALUANDO CON K=10
──────────────────────────────────────────────────────────────────────

======================================================================
📊 EVALUANDO SISTEMA RAG (K=10)
======================================================================

📝 ✅ Tabla users
   Query: CREATE TABLE users con id INT PRIMARY KEY, username VARCHAR, password VARCHAR, e...
   ✅ OK: AP=1.000, Precision@10=0.500

📝 ✅ Tabla books
   Query: CREATE TABLE books con id, title VARCHAR, isbn VARCHAR, pages INT...
   ✅ OK: AP=1.000, Precision@10=1.000

📝 ✅ Tabla genres
   Query: CREATE TABLE genres con id INT, name VARCHAR...
   ✅ OK: AP=1.000, Precision@10=0.600

📝 ✅ Relación books-genres
   Query: CREATE TABLE books_genres con book_id INT, genre_id INT, FOREIGN KEY...
   ✅ OK: AP=1.000, Precision@10=0.400

📝 ✅ Tabla books_authors
   Query: CREATE TABLE books_authors con book_id INT, author_id INT...
   ✅ OK: AP=1.000, Precision@10=0.800

📝 ✅ Múltiples tablas
   Query: CREATE TABLE books, CREATE TABLE authors, CREATE TABLE books_authors con book_id...
   ✅ OK: AP=1.000, Precision@10=1.000

📝 ✅ Tabla reviews
   Query: CREATE TABLE reviews con rating INT, comment TEXT, review_date DATETIME, FOREIGN...
   ✅ OK: AP=1.000, Precision@10=0.200

📝 ❌ Tabla inexistente
   Query: CREATE TABLE inventory con stock INT, location VARCHAR...
   ✅ OK: AP=0.000, Precision@10=0.000

📝 ❌ Tabla shopping_cart
   Query: CREATE TABLE shopping_cart con user_id INT, product_id INT...
   ✅ OK: AP=0.000, Precision@10=0.000

📝 ⚠️ Query ambigua
   Query: tabla para guardar información de personas que usan el sistema con email y contr...
   ✅ OK: AP=1.000, Precision@10=0.500


======================================================================
📈 REPORTE DETALLADO (K=10)
======================================================================

🎯 MÉTRICAS GLOBALES:
   Mean Average Precision (MAP): 0.8000
   Mean Precision@10: 0.5000
   Mean Recall@10: 1.0000
   Mean NDCG@10: 0.8000
   Mean F1-Score: 0.5877
   MRR: 0.8000
   Expectation Rate: 100.00%

📊 POR TIPO DE QUERY:
   Positivas (8):
     - MAP: 1.0000
     - Precision@10: 0.6250
     - Recall@10: 1.0000

   Negativas (2):
     - False Positives: 0
     - Specificity: 100.00%

🎯 HIT RATES:
   Hit Rate@1: 80.00%
   Hit Rate@3: 80.00%
   Hit Rate@5: 80.00%

⚠️ QUERIES PROBLEMÁTICAS:

──────────────────────────────────────────────────────────────────────
🔄 EVALUANDO CON K=20
──────────────────────────────────────────────────────────────────────

======================================================================
📊 EVALUANDO SISTEMA RAG (K=20)
======================================================================

📝 ✅ Tabla users
   Query: CREATE TABLE users con id INT PRIMARY KEY, username VARCHAR, password VARCHAR, e...
   ✅ OK: AP=1.000, Precision@20=0.250

📝 ✅ Tabla books
   Query: CREATE TABLE books con id, title VARCHAR, isbn VARCHAR, pages INT...
   ✅ OK: AP=1.000, Precision@20=0.500

📝 ✅ Tabla genres
   Query: CREATE TABLE genres con id INT, name VARCHAR...
   ✅ OK: AP=1.000, Precision@20=0.300

📝 ✅ Relación books-genres
   Query: CREATE TABLE books_genres con book_id INT, genre_id INT, FOREIGN KEY...
   ✅ OK: AP=1.000, Precision@20=0.200

📝 ✅ Tabla books_authors
   Query: CREATE TABLE books_authors con book_id INT, author_id INT...
   ✅ OK: AP=1.000, Precision@20=0.400

📝 ✅ Múltiples tablas
   Query: CREATE TABLE books, CREATE TABLE authors, CREATE TABLE books_authors con book_id...
   ✅ OK: AP=0.994, Precision@20=0.600

📝 ✅ Tabla reviews
   Query: CREATE TABLE reviews con rating INT, comment TEXT, review_date DATETIME, FOREIGN...
   ✅ OK: AP=1.000, Precision@20=0.100

📝 ❌ Tabla inexistente
   Query: CREATE TABLE inventory con stock INT, location VARCHAR...
   ✅ OK: AP=0.000, Precision@20=0.000

📝 ❌ Tabla shopping_cart
   Query: CREATE TABLE shopping_cart con user_id INT, product_id INT...
   ✅ OK: AP=0.000, Precision@20=0.000

📝 ⚠️ Query ambigua
   Query: tabla para guardar información de personas que usan el sistema con email y contr...
   ✅ OK: AP=1.000, Precision@20=0.250


======================================================================
📈 REPORTE DETALLADO (K=20)
======================================================================

🎯 MÉTRICAS GLOBALES:
   Mean Average Precision (MAP): 0.7994
   Mean Precision@20: 0.2600
   Mean Recall@20: 1.0000
   Mean NDCG@20: 0.7999
   Mean F1-Score: 0.3765
   MRR: 0.8000
   Expectation Rate: 100.00%

📊 POR TIPO DE QUERY:
   Positivas (8):
     - MAP: 0.9992
     - Precision@20: 0.3250
     - Recall@20: 1.0000

   Negativas (2):
     - False Positives: 0
     - Specificity: 100.00%

🎯 HIT RATES:
   Hit Rate@1: 80.00%
   Hit Rate@3: 80.00%
   Hit Rate@5: 80.00%

⚠️ QUERIES PROBLEMÁTICAS:

======================================================================
📊 RESUMEN COMPARATIVO
======================================================================

K	MAP		P@{K}		R@{K}		HIT@1
-----------------------------------------------------------------
5	0.8000		0.7200		1.0000		80.00%
10	0.8000		0.5000		1.0000		80.00%
20	0.7994		0.2600		1.0000		80.00%

======================================================================
💾 GUARDANDO RESULTADOS
======================================================================

💾 Resultados guardados en: /home/pepe/Documents/UNMSM/2025-2/Semanario de Tesis 3/herramienta/tests/20251211_112010_llama3.2:3b_postgres/evaluation_results/evaluation_report_20260501_082734.json
💾 Resumen guardado en: /home/pepe/Documents/UNMSM/2025-2/Semanario de Tesis 3/herramienta/tests/20251211_112010_llama3.2:3b_postgres/evaluation_results/evaluation_summary_20260501_082734.json

✅ Diagnóstico y evaluación completados
📁 Resultados guardados en: /home/pepe/Documents/UNMSM/2025-2/Semanario de Tesis 3/herramienta/tests/20251211_112010_llama3.2:3b_postgres/evaluation_results
   - Reporte completo: evaluation_report_20260501_082734.json
   - Resumen: evaluation_summary_20260501_082734.json