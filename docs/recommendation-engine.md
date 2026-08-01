# Recommendation Engine

El motor inicial es deterministico y deliberadamente pequeno.

## Flujo

1. Obtiene participantes del plan.
2. Obtiene venues disponibles.
3. Calcula costo por participante:

```text
entrada + consumo estimado + transporte estimado
```

4. Marca si cada persona queda dentro de presupuesto.
5. Calcula un score grupal.
6. Retorna ranking ordenado de mayor a menor score.

## Consumo

Los niveles `low`, `medium` y `high` se basan en multiplicadores configurables por variables de entorno:

- `CONSUMPTION_UNITS_LOW`
- `CONSUMPTION_UNITS_MEDIUM`
- `CONSUMPTION_UNITS_HIGH`

`custom` usa el valor medio como fallback inicial.

## Transporte

El transporte usa una tabla simple por combinacion de:

```text
zona de origen + zona del venue + tipo de transporte
```

No se integran precios dinamicos ni APIs externas en esta etapa.

## Scoring

El score combina:

- Porcentaje de participantes dentro de presupuesto.
- Relacion entre costo promedio y presupuesto promedio.
- Coincidencias de musica y ambiente.

El resultado se limita a un rango de 0 a 100.

## Evolucion Esperada

- Agregar restricciones obligatorias antes del scoring.
- Incorporar horarios y deadline de decision.
- Modelar mejor trade-offs por participante.
- Mantener las reglas deterministicas separadas de una futura capa de IA.
