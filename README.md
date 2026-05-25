# Tournament Platform

Plataforma competitiva de torneos online donde equipos pueden registrarse, competir en torneos, consultar rankings en tiempo real y recibir notificaciones automáticas. Construida con arquitectura de microservicios.

---

## Arquitectura

```
┌────────────────────────────────────────────────────┐
│                      Clientes                      │
└──────────────────────────┬─────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
   ┌──────────▼──────────┐  ┌──────────▼──────────┐
   │    django-api       │  │    auth-service     │
   │  Django 4.2 + DRF   │  │  Spring Boot 3.5    │
   │  Python · Port 8000 │  │  Java 17 · Port 8080│
   └──────────┬──────────┘  └─────────────────────┘
              │ valida JWT via HTTP
              │
   ┌──────────▼──────────┐
   │     PostgreSQL      │
   │   Base de datos     │
   └─────────────────────┘
```

El `django-api` delega toda autenticación al `auth-service`: cada request con token Bearer se valida via `POST /auth/validate`.

---

## Servicios

### `django-api` — API REST principal

**Stack:** Python 3.13, Django 4.2, Django REST Framework, django-filter, python-decouple, psycopg2

**Dominio:**

| Módulo | Modelos |
|---|---|
| `users` | `User` (rol: admin / organizer / player, ELO 1000 base), `EloHistory` |
| `teams` | `Team`, `TeamMember` |
| `tournaments` | `Tournament` (formatos: single_elimination / round_robin), `TournamentTeam`, `Match` |

**Endpoints:**

| Recurso | Ruta | Auth requerida |
|---|---|---|
| Torneos | `GET /tournaments/` | No (drafts solo para admin/organizer) |
| Crear torneo | `POST /tournaments/` | Admin |
| Equipos | `GET /teams/` | No |
| Crear equipo | `POST /teams/` | Autenticado |
| Partidas | `GET /matches/` | No |
| Reportar resultado | `POST /matches/{id}/report/` | Autenticado |

**Características transversales:**
- Middleware JWT personalizado (`JwtAuthMiddleware`) — valida contra `auth-service`
- Paginación: `PageNumberPagination` (20 por página, máx 100) para listas generales; `CursorPagination` por `-played_at` para partidas
- Throttling: anónimos 5/min, autenticados 60/min (con header `Retry-After`)
- Filtros: torneos por `status`, `date_from`, `date_to`, `created_by`; partidas por `tournament_id`, `status`, `date_from`, `date_to`, equipos por `tournament_id`
- CORS configurado via `django-cors-headers`
- Settings divididos por entorno: `base`, `development`, `testing`, `production`

---

### `auth-service` — Microservicio de autenticación

**Stack:** Java 17, Spring Boot 3.5, Spring Security, Spring Data JPA, JJWT (jjwt-api), PostgreSQL, H2 (tests)

**Endpoints:**

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/auth/register` | Registro de usuario (roles: admin / organizer / player) |
| `POST` | `/auth/login` | Login — devuelve `access_token` + `refresh_token` |
| `POST` | `/auth/refresh` | Rotación de refresh token (family revocation) |
| `POST` | `/auth/validate` | Valida access token — usado por `django-api` |
| `POST` | `/auth/logout` | Revoca refresh token |

**Características de seguridad:**
- Access tokens JWT firmados con HMAC-SHA256
- `JWT_SECRET` requerido via variable de entorno (mínimo 32 caracteres, validado al arrancar)
- Refresh token rotation con family revocation — reutilizar un token revocado invalida toda la familia
- Contraseñas hasheadas con SHA-256 + salt

---

## Base de datos

**Motor:** PostgreSQL

| Tabla | Descripción |
|---|---|
| `users` | Usuarios con rol y ELO, índice en `elo DESC` |
| `teams` | Equipos, con propietario |
| `team_members` | Relación N:M usuarios-equipos |
| `tournaments` | Torneos con estado y formato |
| `tournament_teams` | Inscripciones equipo-torneo |
| `matches` | Partidas con scores, índices en `tournament_id` y `played_at` |
| `elo_history` | Historial de cambios de ELO por partida |

---

## Testing

| Servicio | Tests | Herramientas |
|---|---|---|
| `django-api` | 207 tests + 4 subtests | pytest, pytest-django, SQLite en memoria |
| `auth-service` | 55 tests | JUnit 5, Mockito, MockMvc, H2 en memoria |

**Metodología:** TDD obligatorio — se escribe el test antes que el código de producción.

**Mutation testing:** `mutmut` configurado en `django-api` (objetivo: score > 95%).

Para correr los tests:

```bash
# django-api
cd django-api
source .venv/bin/activate
pytest

# auth-service
cd auth-service
./mvnw test
```

---

## Variables de entorno

### `django-api`

| Variable | Descripción | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | — |
| `DEBUG` | Modo debug | `True` |
| `DB_NAME` | Nombre de la BD | `tournament_platform` |
| `DB_USER` | Usuario de la BD | — |
| `DB_PASSWORD` | Contraseña de la BD | — |
| `DB_HOST` | Host de la BD | `localhost` |
| `DB_PORT` | Puerto de la BD | `5432` |
| `AUTH_SERVICE_URL` | URL del auth-service | `http://java-auth:8080` |
| `CORS_ALLOWED_ORIGINS` | Orígenes permitidos | `http://localhost:3000,http://localhost:5073` |
| `PAGE_SIZE` | Tamaño de página por defecto | `20` |

### `auth-service`

| Variable | Descripción |
|---|---|
| `JWT_SECRET` | Clave HMAC para firmar tokens (mínimo 32 chars) |
| `SPRING_DATASOURCE_URL` | URL de conexión a PostgreSQL |
| `SPRING_DATASOURCE_USERNAME` | Usuario de la BD |
| `SPRING_DATASOURCE_PASSWORD` | Contraseña de la BD |

---

## Roadmap

El proyecto sigue un roadmap de 8 fases:

| Fase | Estado | Descripción |
|---|---|---|
| 1 — Base del sistema | ✅ Completo | PostgreSQL schema + Django API REST |
| 2 — Seguridad con Java | ✅ Completo | auth-service con JWT, refresh rotation |
| 3 — Docker | Pendiente | Contenerización completa + Nginx |
| 4 — Kafka + Eventos | Pendiente | Mensajería asíncrona entre servicios |
| 5 — Sistema de ranking | Pendiente | ELO automático + PostgreSQL transactions |
| 6 — Tiempo real | Pendiente | Django Channels + WebSockets |
| 7 — Kubernetes | Pendiente | Deploy K8s con Helm e Ingress |
| 8 — Observabilidad | Pendiente | Prometheus + Grafana |
