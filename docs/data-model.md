# Modelo de Datos

## Plan

Representa una salida que el grupo quiere organizar. Contiene fecha, hora aproximada, zona preferida, tipo de panorama y estado.

## Participant

Representa a una persona dentro de un plan. Incluye presupuesto, precio maximo de entrada, zona de origen, tipo de transporte, nivel de consumo, preferencias y restricciones.

`preferences` y `restrictions` se guardan como JSON para permitir evolucionar el cuestionario sin migraciones frecuentes.

## Venue

Representa un lugar del catalogo controlado. Incluye zona, coordenadas, precios, horarios, edad minima, etiquetas musicales, etiquetas de ambiente y caracteristicas adicionales.

Las etiquetas se modelan como JSON para mantener compatibilidad sencilla con PostgreSQL y SQLite durante pruebas.

## Recommendation

Representa el resultado de evaluar un lugar para un plan. Guarda score, categoria, costo promedio estimado, tiempos promedio, razones y trade-offs.

## ParticipantCost

Detalle por participante para una recomendacion. Permite explicar por que una opcion queda dentro o fuera de presupuesto para cada persona.
