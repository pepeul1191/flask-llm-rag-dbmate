# Detección de errores estructurales inyectados

DB tipo: `sqlite`. Cada celda = TP/(TP+FN) por tipo de error. `FP(clean)` = falsos positivos sobre el baseline sin errores (0 es lo ideal).

| Schema | dTable | dCol | cType | dPK | dFK | rTable | FP(clean) | P | R | F1 |
|---|---|---|---|---|---|---|---|---|---|---|
| basico | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0 | 1.000 | 1.000 | 1.000 |
| biblio | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0 | 1.000 | 1.000 | 1.000 |
| innova | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0 | 1.000 | 1.000 | 1.000 |
| northwind | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0 | 1.000 | 1.000 | 1.000 |
| postulaciones | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0 | 1.000 | 1.000 | 1.000 |
