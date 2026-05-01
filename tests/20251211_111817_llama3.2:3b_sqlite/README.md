# Migraciones SQL - biblio

**Fecha de generación:** 2025-12-11 11:18:17
**Tipo de base de datos:** sqlite
**Archivo PUML origen:** biblio.puml
**Total de tablas generadas:** 10

## Estructura de carpetas

- `migrations/` - Archivos individuales de migración
- `complete_migrations_*.sql` - Todas las migraciones en un archivo
- `metadata.json` - Información de generación
- `README.md` - Este archivo

## Tablas generadas

1. `users`
2. `countries`
3. `devices`
4. `books`
5. `publishers`
6. `authors`
7. `genres`
8. `reviews`
9. `books_authors`
10. `books_genres`


## RESULTADOS

(venv) pepe@pepe-30fns02m00:~/Documents/UNMSM/2025-2/Semanario de Tesis 3/herramienta/tests/20251211_111817_llama3.2:3b_sqlite$ python3 test.py

======================================================================
🔍 DIAGNÓSTICO Y EVALUACIÓN DEL SISTEMA RAG
======================================================================

💾 Total de chunks en ChromaDB: 10

──────────────────────────────────────────────────────────────────────
🔄 EVALUANDO CON K=5
──────────────────────────────────────────────────────────────────────

======================================================================
📊 EVALUANDO SISTEMA RAG (K=5)
======================================================================

📝 ✅ Tabla users
   Query: CREATE TABLE users con id INT PRIMARY KEY, username VARCHAR, password VARCHAR, e...
   ✅ OK: AP=0.917, Precision@5=0.600

📝 ✅ Tabla books
   Query: CREATE TABLE books con id, title VARCHAR, isbn VARCHAR, pages INT...
   ✅ OK: AP=0.950, Precision@5=0.800

📝 ✅ Tabla genres
   Query: CREATE TABLE genres con id INT, name VARCHAR...
   ✅ OK: AP=1.000, Precision@5=0.400

📝 ✅ Relación books-genres
   Query: CREATE TABLE books_genres con book_id INT, genre_id INT, FOREIGN KEY...
   ✅ OK: AP=1.000, Precision@5=0.200

📝 ✅ Tabla books_authors
   Query: CREATE TABLE books_authors con book_id INT, author_id INT...
   ✅ OK: AP=1.000, Precision@5=0.200

📝 ✅ Múltiples tablas
   Query: CREATE TABLE books, CREATE TABLE authors, CREATE TABLE books_authors con book_id...
   ✅ OK: AP=1.000, Precision@5=1.000

📝 ✅ Tabla reviews
   Query: CREATE TABLE reviews con rating INT, comment TEXT, review_date DATETIME, FOREIGN...
   ✅ OK: AP=1.000, Precision@5=0.200

📝 ❌ Tabla inexistente
   Query: CREATE TABLE inventory con stock INT, location VARCHAR...
   ✅ OK: AP=0.000, Precision@5=0.000

📝 ❌ Tabla shopping_cart
   Query: CREATE TABLE shopping_cart con user_id INT, product_id INT...
   ✅ OK: AP=0.000, Precision@5=0.000

📝 ⚠️ Query ambigua
   Query: tabla para guardar información de personas que usan el sistema con email y contr...
   ✅ OK: AP=1.000, Precision@5=0.600


======================================================================
📈 REPORTE DETALLADO (K=5)
======================================================================

🎯 MÉTRICAS GLOBALES:
   Mean Average Precision (MAP): 0.7867
   Mean Precision@5: 0.4000
   Mean Recall@5: 1.0000
   Mean NDCG@5: 0.7950
   Mean F1-Score: 0.4960
   MRR: 0.8000
   Expectation Rate: 100.00%

📊 POR TIPO DE QUERY:
   Positivas (8):
     - MAP: 0.9833
     - Precision@5: 0.5000
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
   ✅ OK: AP=0.917, Precision@10=0.300

📝 ✅ Tabla books
   Query: CREATE TABLE books con id, title VARCHAR, isbn VARCHAR, pages INT...
   ✅ OK: AP=0.950, Precision@10=0.400

📝 ✅ Tabla genres
   Query: CREATE TABLE genres con id INT, name VARCHAR...
   ✅ OK: AP=1.000, Precision@10=0.200

📝 ✅ Relación books-genres
   Query: CREATE TABLE books_genres con book_id INT, genre_id INT, FOREIGN KEY...
   ✅ OK: AP=1.000, Precision@10=0.100

📝 ✅ Tabla books_authors
   Query: CREATE TABLE books_authors con book_id INT, author_id INT...
   ✅ OK: AP=1.000, Precision@10=0.100

📝 ✅ Múltiples tablas
   Query: CREATE TABLE books, CREATE TABLE authors, CREATE TABLE books_authors con book_id...
   ✅ OK: AP=1.000, Precision@10=0.500

📝 ✅ Tabla reviews
   Query: CREATE TABLE reviews con rating INT, comment TEXT, review_date DATETIME, FOREIGN...
   ✅ OK: AP=1.000, Precision@10=0.100

📝 ❌ Tabla inexistente
   Query: CREATE TABLE inventory con stock INT, location VARCHAR...
   ✅ OK: AP=0.000, Precision@10=0.000

📝 ❌ Tabla shopping_cart
   Query: CREATE TABLE shopping_cart con user_id INT, product_id INT...
   ✅ OK: AP=0.000, Precision@10=0.000

📝 ⚠️ Query ambigua
   Query: tabla para guardar información de personas que usan el sistema con email y contr...
   ✅ OK: AP=1.000, Precision@10=0.300


======================================================================
📈 REPORTE DETALLADO (K=10)
======================================================================

🎯 MÉTRICAS GLOBALES:
   Mean Average Precision (MAP): 0.7867
   Mean Precision@10: 0.2000
   Mean Recall@10: 1.0000
   Mean NDCG@10: 0.7950
   Mean F1-Score: 0.3040
   MRR: 0.8000
   Expectation Rate: 100.00%

📊 POR TIPO DE QUERY:
   Positivas (8):
     - MAP: 0.9833
     - Precision@10: 0.2500
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
   ✅ OK: AP=0.917, Precision@20=0.150

📝 ✅ Tabla books
   Query: CREATE TABLE books con id, title VARCHAR, isbn VARCHAR, pages INT...
   ✅ OK: AP=0.950, Precision@20=0.200

📝 ✅ Tabla genres
   Query: CREATE TABLE genres con id INT, name VARCHAR...
   ✅ OK: AP=1.000, Precision@20=0.100

📝 ✅ Relación books-genres
   Query: CREATE TABLE books_genres con book_id INT, genre_id INT, FOREIGN KEY...
   ✅ OK: AP=1.000, Precision@20=0.050

📝 ✅ Tabla books_authors
   Query: CREATE TABLE books_authors con book_id INT, author_id INT...
   ✅ OK: AP=1.000, Precision@20=0.050

📝 ✅ Múltiples tablas
   Query: CREATE TABLE books, CREATE TABLE authors, CREATE TABLE books_authors con book_id...
   ✅ OK: AP=1.000, Precision@20=0.250

📝 ✅ Tabla reviews
   Query: CREATE TABLE reviews con rating INT, comment TEXT, review_date DATETIME, FOREIGN...
   ✅ OK: AP=1.000, Precision@20=0.050

📝 ❌ Tabla inexistente
   Query: CREATE TABLE inventory con stock INT, location VARCHAR...
   ✅ OK: AP=0.000, Precision@20=0.000

📝 ❌ Tabla shopping_cart
   Query: CREATE TABLE shopping_cart con user_id INT, product_id INT...
   ✅ OK: AP=0.000, Precision@20=0.000

📝 ⚠️ Query ambigua
   Query: tabla para guardar información de personas que usan el sistema con email y contr...
   ✅ OK: AP=1.000, Precision@20=0.150


======================================================================
📈 REPORTE DETALLADO (K=20)
======================================================================

🎯 MÉTRICAS GLOBALES:
   Mean Average Precision (MAP): 0.7867
   Mean Precision@20: 0.1000
   Mean Recall@20: 1.0000
   Mean NDCG@20: 0.7950
   Mean F1-Score: 0.1723
   MRR: 0.8000
   Expectation Rate: 100.00%

📊 POR TIPO DE QUERY:
   Positivas (8):
     - MAP: 0.9833
     - Precision@20: 0.1250
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
5	0.7867		0.4000		1.0000		80.00%
10	0.7867		0.2000		1.0000		80.00%
20	0.7867		0.1000		1.0000		80.00%

======================================================================
💾 GUARDANDO RESULTADOS
======================================================================

💾 Resultados guardados en: /home/pepe/Documents/UNMSM/2025-2/Semanario de Tesis 3/herramienta/tests/20251211_111817_llama3.2:3b_sqlite/evaluation_results/evaluation_report_20260501_081801.json
💾 Resumen guardado en: /home/pepe/Documents/UNMSM/2025-2/Semanario de Tesis 3/herramienta/tests/20251211_111817_llama3.2:3b_sqlite/evaluation_results/evaluation_summary_20260501_081801.json

✅ Diagnóstico y evaluación completados
📁 Resultados guardados en: /home/pepe/Documents/UNMSM/2025-2/Semanario de Tesis 3/herramienta/tests/20251211_111817_llama3.2:3b_sqlite/evaluation_results
   - Reporte completo: evaluation_report_20260501_081801.json
   - Resumen: evaluation_summary_20260501_081801.json