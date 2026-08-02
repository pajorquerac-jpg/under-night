# Guion de presentacion - UnderNight MVP

## Slide 1 - Titulo

UnderNight: recomendaciones explicables para decidir donde salir en grupo.

Mensaje clave: el producto ordena presupuesto, gustos, zonas y traslados para que el grupo tome una mejor decision.

## Slide 2 - Problema

Organizar una salida nocturna en grupo es dificil porque cada persona tiene restricciones distintas. El costo real mezcla entrada, consumo y traslado, y la decision suele tomarse en un chat sin comparacion clara.

## Slide 3 - Propuesta de valor

UnderNight convierte preferencias dispersas en un ranking de lugares. Cada recomendacion muestra compatibilidad, costo promedio, detalle por amigo y trade-offs.

## Slide 4 - Experiencia del usuario

Flujo principal:

1. El usuario inicia una salida.
2. El asistente pregunta datos base.
3. La app muestra progreso.
4. Cuando los datos estan completos, calcula recomendaciones.
5. El grupo revisa ranking, mapa, costos y razones.

## Slide 5 - Arquitectura del MVP

Usar el diagrama "Arquitectura de alto nivel" de `docs/diagrams.md`.

Puntos a explicar:

- Mobile solo captura y visualiza.
- Backend concentra reglas y persistencia.
- PostgreSQL guarda planes, participantes, venues, recomendaciones y conversaciones.
- Ollama es opcional; el sistema conserva fallback por reglas.

## Slide 6 - Modelo de datos

Usar el diagrama entidad-relacion de `docs/diagrams.md`.

Puntos a explicar:

- `Plan` agrupa la salida.
- `Participant` guarda presupuesto, zona, transporte y gustos.
- `Venue` representa el catalogo.
- `Recommendation` guarda el ranking.
- `ParticipantCost` explica el costo individual.
- `Conversation` permite continuidad del asistente.

## Slide 7 - Motor de recomendaciones

Formula base:

```text
costo_total = entrada + consumo_estimado + transporte_estimado
```

Score:

```text
ratio en presupuesto + asequibilidad + preferencias
```

Mensaje clave: el motor es deterministico, auditable y explicable. La IA no decide el ranking.

## Slide 8 - Agente conversacional

Usar el diagrama "Flujo conversacional" de `docs/diagrams.md`.

Puntos a explicar:

- Extrae datos del lenguaje natural.
- Normaliza fechas relativas.
- Mantiene estado y campos faltantes.
- Pregunta de a un dato principal.
- Usa Ollama si esta disponible, pero puede operar por reglas.

## Slide 9 - Demo de datos

El seed carga venues ficticios con distintos casos:

- Opcion economica.
- Alta compatibilidad pero costo mayor.
- Lugar premium.
- Datos desactualizados.
- Edad minima mas alta.

Esto permite demostrar ranking, viabilidad y trade-offs sin depender de integraciones externas.

## Slide 10 - Estado actual y limitaciones

Incluido:

- App mobile funcional.
- API REST.
- Persistencia.
- Recomendaciones explicables.
- Chat con estado.
- Mapas y enlaces externos.

Limitaciones:

- Catalogo ficticio.
- Sin usuarios ni reservas.
- Transporte y precios estaticos.
- Restricciones aun no filtran todos los casos.
- Sin despliegue productivo.

## Slide 11 - Roadmap

Proximos pasos:

- Participantes por invitacion.
- Catalogo real de venues.
- Restricciones duras antes del scoring.
- Mejor explicacion de ajustes necesarios.
- Versionado del algoritmo.
- Observabilidad y despliegue.

## Slide 12 - Cierre

UnderNight reduce la friccion de decidir una salida grupal. El MVP demuestra la arquitectura base: captura conversacional, datos estructurados, recomendacion deterministica y explicacion por participante.
