# Diagramas de arquitectura

Este archivo contiene diagramas Mermaid listos para pegar en Markdown, Notion, GitHub, presentaciones compatibles o herramientas como Mermaid Live Editor.

## 1. Arquitectura de alto nivel

```mermaid
flowchart LR
    subgraph Client["Mobile App"]
        Home[Home]
        Chat[Agent Chat]
        Form[Quick Questionnaire]
        Recs[Recommendations + Map]
    end

    subgraph API["FastAPI Backend"]
        Routes[API v1 Routes]
        Schemas[Pydantic Schemas]
        Services[Services]
        Repos[Repositories]
        Engine[Recommendation Engine]
        Agent[Conversation Agent]
    end

    subgraph Data["Data Layer"]
        DB[(PostgreSQL)]
        Alembic[Alembic Migrations]
        Seed[Seed Data]
    end

    subgraph OptionalAI["Optional Local AI"]
        Ollama[Ollama]
    end

    Home --> Chat
    Home --> Recs
    Chat -->|REST JSON| Routes
    Form -->|REST JSON| Routes
    Recs -->|REST JSON| Routes
    Routes --> Schemas
    Routes --> Services
    Services --> Engine
    Services --> Agent
    Services --> Repos
    Repos --> DB
    Alembic --> DB
    Seed --> DB
    Agent -.-> Ollama
```

## 2. Capas del backend

```mermaid
flowchart TD
    HTTP[HTTP Request] --> Endpoint[FastAPI Endpoint]
    Endpoint --> SchemaIn[Pydantic Input Schema]
    SchemaIn --> Service[Service / Use Case]
    Service --> Repository[Repository]
    Repository --> Model[SQLAlchemy Model]
    Model --> Database[(PostgreSQL)]
    Service --> Domain[Domain Rules / Recommendation Engine]
    Domain --> Repository
    Repository --> SchemaOut[Pydantic Response Schema]
    SchemaOut --> HTTPResponse[HTTP JSON Response]
```

## 3. Flujo conversacional

```mermaid
sequenceDiagram
    participant U as Usuario
    participant M as Mobile Chat
    participant A as Agent Endpoint
    participant O as Ollama opcional
    participant DB as PostgreSQL

    U->>M: escribe mensaje
    M->>A: POST /api/v1/agent/chat
    A->>DB: get_or_create_conversation
    A->>DB: guarda mensaje user
    alt use_llm=true y Ollama disponible
        A->>O: extrae JSON estructurado
        O-->>A: datos extraidos
    else fallback
        A->>A: extraccion por reglas
    end
    A->>A: normaliza fecha y fusiona estado
    A->>A: calcula missing_fields y stage
    alt datos completos
        A->>A: sugiere calcular recomendaciones
    else faltan datos
        A->>A: pregunta siguiente campo
    end
    A->>DB: guarda estado y respuesta assistant
    A-->>M: AgentChatResponse
    M-->>U: respuesta, progreso y acciones
```

## 4. Flujo de recomendaciones

```mermaid
flowchart TD
    Start[Solicitud de recomendaciones] --> Validate[Validar payload o plan_id]
    Validate --> Plan[Crear/leer Plan]
    Plan --> Participants[Crear/leer Participants]
    Participants --> Venues[Leer Venue catalog]
    Venues --> Estimate[Estimar costos por participante]
    Estimate --> Budget[Evaluar presupuesto y entrada maxima]
    Budget --> Preferences[Calcular coincidencias de musica y ambiente]
    Preferences --> Score[Calcular score 0-100]
    Score --> Rank[Ordenar venues por score]
    Rank --> Persist[Guardar Recommendation y ParticipantCost]
    Persist --> Response[Responder ranking explicable]
```

## 5. Modelo entidad-relacion

```mermaid
erDiagram
    PLAN ||--o{ PARTICIPANT : contains
    PLAN ||--o{ RECOMMENDATION : has
    VENUE ||--o{ RECOMMENDATION : ranks
    RECOMMENDATION ||--o{ PARTICIPANT_COST : includes
    PARTICIPANT ||--o{ PARTICIPANT_COST : receives
    CONVERSATION ||--o{ CONVERSATION_MESSAGE : has

    PLAN {
        int id PK
        string name
        date event_date
        time start_time
        datetime decision_deadline
        string preferred_zone
        string plan_type
        string status
    }

    PARTICIPANT {
        int id PK
        int plan_id FK
        string name
        decimal budget
        decimal max_entry_price
        string origin_zone
        string transport_type
        string consumption_level
        json preferences
        json restrictions
    }

    VENUE {
        int id PK
        string name
        string zone
        float latitude
        float longitude
        decimal entry_price
        decimal average_drink_price
        time opening_time
        time closing_time
        int minimum_age
        json music_tags
        json ambience_tags
        json features
    }

    RECOMMENDATION {
        int id PK
        int plan_id FK
        int venue_id FK
        float score
        string category
        decimal estimated_average_cost
        boolean all_within_budget
        int average_travel_minutes
        json reasons
        json tradeoffs
    }

    PARTICIPANT_COST {
        int id PK
        int recommendation_id FK
        int participant_id FK
        decimal entry_cost
        decimal consumption_cost
        decimal transport_cost
        decimal total_cost
        decimal remaining_budget
        boolean within_budget
    }

    CONVERSATION {
        string id PK
        json state
        string stage
    }

    CONVERSATION_MESSAGE {
        int id PK
        string conversation_id FK
        string role
        string content
        string provider
        string model
    }
```

## 6. Arquitectura de despliegue local

```mermaid
flowchart LR
    Dev[Developer Machine] --> Expo[Expo Dev Server]
    Dev --> Compose[Docker Compose]
    Compose --> API[API Container]
    Compose --> Postgres[(Postgres Container)]
    API --> Postgres
    API -. host.docker.internal:11434 .-> Ollama[Ollama local]
    Phone[Expo Go / Simulator] -->|EXPO_PUBLIC_API_URL| API
```

## 7. Decision tree de viabilidad

```mermaid
flowchart TD
    Venue[Venue evaluado] --> Each[Por cada participante]
    Each --> Cost[entrada + consumo + traslado]
    Cost --> EntryOk{entrada <= entrada maxima?}
    EntryOk -->|no| Over[fuera de presupuesto]
    EntryOk -->|si| BudgetOk{costo_total <= presupuesto?}
    BudgetOk -->|no| Over
    BudgetOk -->|si| Within[dentro de presupuesto]
    Within --> Group[Resumen grupal]
    Over --> Group
    Group --> All{todos dentro?}
    All -->|si| Viable[viable]
    All -->|no, algunos| Partial[parcialmente viable]
    All -->|no, ninguno| NotViable[no viable]
```
