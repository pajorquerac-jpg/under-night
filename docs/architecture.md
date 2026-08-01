# Arquitectura

UnderNight usa un monorepo simple:

- `apps/mobile`: aplicacion React Native con Expo, Expo Router y TypeScript.
- `apps/api`: backend FastAPI con SQLAlchemy, Alembic y PostgreSQL.
- `infrastructure`: espacio para configuraciones de despliegue o proxy.
- `docs`: documentacion del producto y decisiones tecnicas.

La API expone endpoints REST versionados bajo `/api/v1`. Los endpoints delegan en repositorios y servicios para mantener la logica de negocio fuera de las rutas.

El motor de recomendaciones vive en `app/recommendation`. En esta etapa contiene reglas deterministicas de estimacion y scoring. La intencion es que una futura capa de IA pueda explicar o enriquecer resultados sin reemplazar las restricciones duras ni la logica auditable.
