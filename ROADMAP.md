# 🏆 Tournament Platform — Roadmap Completo

> **ES:** Plataforma competitiva de torneos online donde equipos pueden registrarse, competir en torneos, consultar rankings en tiempo real y recibir notificaciones automáticas. Construida con arquitectura de microservicios usando Django, Java, Kafka y Kubernetes.
>
> **EN:** A competitive online tournament platform where teams can register, compete in tournaments, track live rankings and receive automated notifications. Built with a microservices architecture using Django, Java, Kafka and Kubernetes.

---

## Tecnologías principales

| Tecnología | Rol |
|---|---|
| **PostgreSQL** | Base de datos principal |
| **Django + DRF** | Backend API REST |
| **Java + Spring Boot** | Microservicio de autenticación |
| **Kafka** | Eventos y mensajería asíncrona |
| **Redis** | Cache y channel layer para WebSockets |
| **Docker** | Contenerización del stack |
| **Kubernetes** | Despliegue y escalado en producción |
| **Prometheus + Grafana** | Monitoreo y observabilidad |

---

## Resumen del roadmap

| Fase | Nombre | Semanas | Tecnologías |
|---|---|---|---|
| 1 | Base del sistema | 1 – 3 | PostgreSQL, Django, DRF |
| 2 | Seguridad con Java | 4 – 5 | Java, Spring Boot, JWT |
| 3 | Docker | 6 – 7 | Docker, docker-compose, Nginx |
| 4 | Kafka + Eventos | 8 – 9 | Kafka, Zookeeper |
| 5 | Sistema de ranking | 10 – 11 | ELO, PostgreSQL transactions |
| 6 | Tiempo real | 12 – 13 | Django Channels, WebSockets |
| 7 | Kubernetes | 14 – 16 | K8s, Helm, Ingress |
| 8 | Observabilidad | 17 – 18 | Prometheus, Grafana |

---

## Fase 1 — Base del sistema
**Semanas 1 a 3 · PostgreSQL + Django + DRF**

### Objetivo
Diseñar la base de datos y construir la API REST principal. Es la fase más importante del proyecto: un schema mal diseñado aquí generará migraciones costosas en todas las fases siguientes.

### Tarea 1 · Diseñar el schema de base de datos

Antes de escribir código, diseña el ERD completo con las siguientes tablas:

| Tabla | Campos principales |
|---|---|
| `users` | id, username, email, password_hash, role, elo, created_at |
| `teams` | id, name, owner_id (FK → users), created_at |
| `team_members` | user_id, team_id, joined_at — tabla puente N:M |
| `tournaments` | id, name, status, format, max_teams, start_date, end_date |
| `tournament_teams` | tournament_id, team_id, registered_at — inscripciones |
| `matches` | id, tournament_id, team_a_id, team_b_id, winner_team_id, score_a, score_b, status, played_at |

**Índices a crear:**
- `users.elo` — para ordenar el ranking rápidamente
- `matches.tournament_id` — para filtrar partidas por torneo
- `matches.played_at` — para historial cronológico

**Constraints importantes:**
- `winner_team_id` debe ser `team_a_id` o `team_b_id`, o NULL si la partida no ha terminado. Impleméntalo con un `CHECK` constraint en PostgreSQL.

### Tarea 2 · Practicar queries avanzadas en SQL

Antes de delegar todo al ORM de Django, escribe y entiende estas queries directamente en `psql`:

```sql
-- Ranking global de jugadores
SELECT username, elo
FROM users
ORDER BY elo DESC
LIMIT 50;

-- Equipos con más victorias
SELECT t.name, COUNT(m.id) AS wins
FROM teams t
JOIN matches m ON m.winner_team_id = t.id
GROUP BY t.name
ORDER BY wins DESC;

-- Partidas de un torneo con nombres de equipos
SELECT
  m.id,
  ta.name AS team_a,
  tb.name AS team_b,
  w.name  AS winner,
  m.score_a,
  m.score_b
FROM matches m
JOIN teams ta ON ta.id = m.team_a_id
JOIN teams tb ON tb.id = m.team_b_id
LEFT JOIN teams w ON w.id = m.winner_team_id
WHERE m.tournament_id = 1;
```

### Tarea 3 · Configurar el proyecto Django

```
django-admin startproject tournament_api
python manage.py startapp core
```

- Configura `settings.py` con PostgreSQL (`psycopg2`), CORS y DRF.
- Usa `AbstractBaseUser` para el modelo `User` — cambiarlo después de tener datos es muy costoso.
- Crea los modelos reflejando el schema y corre las migraciones.
- Crea un `management command` para generar datos de prueba.

### Tarea 4 · Construir los endpoints de la API

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/users/` | Listar usuarios |
| GET | `/api/teams/` | Listar equipos |
| POST | `/api/teams/` | Crear equipo |
| GET | `/api/tournaments/` | Listar torneos (`?status=open`) |
| POST | `/api/tournaments/` | Crear torneo |
| GET | `/api/matches/` | Listar partidas (`?tournament_id=X`) |
| POST | `/api/matches/{id}/report/` | Reportar resultado |

**Configuraciones DRF a aplicar:**
- Paginación global: `PAGE_SIZE = 20`
- Filtros con `django-filter`: `?status=open`, `?tournament_id=X`
- Throttling: 100 req/hora anónimos, 1000 autenticados
- Serializers separados por dirección: `input.py` (entrada) y `output.py` (salida)
- JWT básico con `djangorestframework-simplejwt` — se reemplazará en Fase 2

---

## Fase 2 — Seguridad con Java
**Semanas 4 a 5 · Java + Spring Boot + JWT**

### Objetivo
Extraer la autenticación a un microservicio independiente. Django delega completamente la emisión de tokens a este servicio. Esto enseña cómo se separan responsabilidades en una arquitectura de microservicios real.

### Tarea 1 · Crear el proyecto Spring Boot

Genera el proyecto en [start.spring.io](https://start.spring.io) con:
- Java 17, Maven
- Dependencias: Spring Web, Spring Security, Spring Data JPA, PostgreSQL Driver

El servicio Java comparte la misma base de datos PostgreSQL que Django. Solo gestiona los campos de autenticación: `email`, `password_hash`, `role`.

### Tarea 2 · Implementar hashing y JWT

**Endpoints a crear:**

| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/auth/register` | Registra usuario con password hasheado |
| POST | `/auth/login` | Devuelve access token + refresh token |
| POST | `/auth/refresh` | Genera nuevo access token |
| POST | `/auth/logout` | Invalida el refresh token |
| POST | `/auth/validate` | Valida un token (llamado por Django) |

**Reglas de seguridad:**
- Passwords hasheados con `BCryptPasswordEncoder`, nunca en texto plano
- Access token: expira en **15 minutos**
- Refresh token: expira en **7 días**, guardado en DB, puede ser revocado
- Secret JWT leído de variable de entorno, nunca hardcodeado

### Tarea 3 · Conectar Django con el servicio Java

Crea un middleware en Django que:
1. Extrae el Bearer token del header `Authorization`
2. Llama internamente a `http://java-auth:8080/auth/validate`
3. Si el token es válido, inyecta `{userId, email, role}` en `request.user`
4. Si el token es inválido o expiró, devuelve `401` inmediatamente

Una vez integrado, elimina `djangorestframework-simplejwt` — Java es ahora la única fuente de verdad de autenticación.

---

## Fase 3 — Docker
**Semanas 6 a 7 · Docker + docker-compose + Nginx**

### Objetivo
Que cualquier desarrollador pueda levantar el stack completo con un solo comando, en cualquier máquina, sin instalar dependencias manualmente.

### Tarea 1 · Crear los Dockerfiles

**Django:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

**Java:**
```dockerfile
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY target/auth-service.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

### Tarea 2 · Orquestar con docker-compose

Servicios en el `docker-compose.yml`:

| Servicio | Imagen | Puerto interno |
|---|---|---|
| `postgres` | postgres:15 | 5432 |
| `redis` | redis:7-alpine | 6379 |
| `zookeeper` | confluentinc/cp-zookeeper | 2181 |
| `kafka` | confluentinc/cp-kafka | 9092 |
| `django-api` | build local | 8000 |
| `java-auth` | build local | 8080 |
| `nginx` | nginx:alpine | **80** (único público) |

**Reglas:**
- Define una red interna `app-network` — los servicios se comunican por nombre
- Volumen persistente para PostgreSQL — los datos no se borran al reiniciar
- Todas las credenciales en `.env`, nunca en el `docker-compose.yml`
- Añade `.env` al `.gitignore` y provee `.env.example` como plantilla

### Tarea 3 · Configurar Nginx como API Gateway

```nginx
location /api/ {
    proxy_pass http://django-api:8000;
}
location /auth/ {
    proxy_pass http://java-auth:8080;
}
```

Solo Nginx tiene puerto expuesto al exterior. Django y Java son invisibles desde fuera.

---

## Fase 4 — Kafka + Eventos
**Semanas 8 a 9 · Kafka + Zookeeper + Consumers**

### Objetivo
Desacoplar los servicios usando eventos asíncronos. Cuando termina una partida, Django publica un evento y múltiples consumers reaccionan de forma independiente sin que Django sepa quién los escucha.

### Conceptos clave

| Concepto | Definición |
|---|---|
| **Topic** | Cola de mensajes por tipo de evento |
| **Producer** | Publica mensajes en un topic |
| **Consumer** | Lee y procesa mensajes de un topic |
| **Consumer group** | Grupo de consumers que comparten el offset |
| **Offset** | Posición del consumer en el topic |

### Tarea 1 · Topics del sistema

| Topic | Publicado cuando |
|---|---|
| `match.finished` | Se reporta el resultado de una partida |
| `tournament.created` | Se crea un torneo nuevo |
| `user.registered` | Un usuario completa el registro |
| `team.created` | Se crea un equipo |

### Tarea 2 · Django como producer

```python
# Instalar: confluent-kafka
from confluent_kafka import Producer
import json

def publish_event(topic: str, payload: dict):
    producer.produce(
        topic,
        value=json.dumps(payload).encode('utf-8')
    )
    producer.flush()
```

**Regla crítica:** publica el evento **después** de hacer el commit a la base de datos. Si publicas antes y falla el guardado, tendrás eventos huérfanos.

### Tarea 3 · Consumers independientes

| Consumer | Topic que escucha | Qué hace |
|---|---|---|
| `ranking-consumer` | `match.finished` | Dispara recálculo de ELO |
| `notification-consumer` | `match.finished` | Notifica a los equipos |
| `log-consumer` | todos | Guarda historial en `event_log` |

Cada consumer corre en un proceso separado con su propio consumer group para que Kafka lleve el offset de forma independiente.

---

## Fase 5 — Sistema de ranking
**Semanas 10 a 11 · Algoritmo ELO + PostgreSQL transactions**

### Objetivo
Calcular el ranking ELO tras cada partida con consistencia total: si algo falla a mitad del proceso, ningún jugador queda con ELO incorrecto.

### Tarea 1 · Algoritmo ELO

```python
def calculate_elo(elo_winner: int, elo_loser: int, k: int = 32):
    expected_winner = 1 / (1 + 10 ** ((elo_loser - elo_winner) / 400))
    expected_loser  = 1 - expected_winner

    new_elo_winner = round(elo_winner + k * (1 - expected_winner))
    new_elo_loser  = round(elo_loser  + k * (0 - expected_loser))

    return new_elo_winner, new_elo_loser
```

`K = 32` es el factor de cambio estándar. Cuanto mayor la diferencia de ELO, menos puntos gana el favorito al ganar y más pierde al perder.

### Tarea 2 · Transacciones atómicas

```python
from django.db import transaction

@transaction.atomic
def update_elo(match: Match):
    # SELECT FOR UPDATE bloquea las filas durante la transacción
    # Evita que dos partidas simultáneas calculen sobre el mismo ELO base
    winner = User.objects.select_for_update().get(id=match.winner_team_id)
    loser  = User.objects.select_for_update().get(id=match.loser_team_id)

    new_winner_elo, new_loser_elo = calculate_elo(winner.elo, loser.elo)

    winner.elo = new_winner_elo
    loser.elo  = new_loser_elo
    winner.save()
    loser.save()

    # Guarda historial de cambios
    EloHistory.objects.create(user=winner, match=match,
        elo_before=..., elo_after=new_winner_elo)
```

### Tarea 3 · Endpoints de ranking

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/rankings/` | Ranking global paginado |
| GET | `/api/rankings/?tournament_id=X` | Ranking dentro de un torneo |
| GET | `/api/users/{id}/elo-history/` | Historial de ELO de un usuario |

Verifica que la query usa el índice con `EXPLAIN ANALYZE` en psql. Si aparece `Seq Scan`, el índice no está funcionando.

---

## Fase 6 — Tiempo real
**Semanas 12 a 13 · Django Channels + WebSockets + Redis**

### Objetivo
Añadir comunicación en vivo: chat por torneo y actualización de resultados sin recargar la página.

### Tarea 1 · Configurar Django Channels

```python
# requirements
channels
channels-redis

# config/asgi.py
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
```

Redis actúa como channel layer: permite que el broadcast llegue a todos los workers, no solo al que recibió la conexión.

### Tarea 2 · Chat por torneo

**Rutas WebSocket:**
- `ws/tournaments/{id}/chat/` — chat en tiempo real
- `ws/tournaments/{id}/live/` — resultados en vivo

**Ciclo de vida del consumer:**
1. `connect()` — autentica el token, añade el canal al grupo del torneo
2. `receive()` — recibe mensaje, lo guarda en DB, hace broadcast al grupo
3. `disconnect()` — elimina el canal del grupo

Guarda los mensajes en DB aunque sea tiempo real: los usuarios que entran tarde necesitan ver el historial.

### Tarea 3 · Resultados en vivo

Cuando el consumer de Kafka procesa `match.finished`, además de actualizar el ELO, hace broadcast WebSocket al grupo del torneo:

```python
await channel_layer.group_send(
    f"tournament_{tournament_id}",
    {
        "type": "match_update",
        "match_id": match_id,
        "score_a": score_a,
        "score_b": score_b,
        "winner": winner_name,
    }
)
```

El frontend escucha este mensaje y actualiza el marcador sin recargar la página.

---

## Fase 7 — Kubernetes
**Semanas 14 a 16 · Kubernetes + Helm + Ingress**

### Objetivo
Desplegar el sistema en un cluster con alta disponibilidad, escalado automático y cero downtime en deploys.

### Conceptos clave

| Recurso | Qué hace |
|---|---|
| **Pod** | Unidad mínima: uno o varios contenedores |
| **Deployment** | Gestiona pods y garantiza las réplicas configuradas |
| **Service** | Expone un Deployment internamente por nombre |
| **Ingress** | Punto de entrada externo, enruta tráfico a Services |
| **ConfigMap** | Configuración no sensible (hosts, puertos) |
| **Secret** | Credenciales (base64, o gestor externo en producción) |

### Tarea 1 · Manifiestos de despliegue

| Servicio | Réplicas | Motivo |
|---|---|---|
| `django-api` | 3 | Alta disponibilidad de la API |
| `java-auth` | 2 | Redundancia del servicio de auth |
| `kafka` | StatefulSet | Requiere identidad de red estable |

### Tarea 2 · Probes de salud

```yaml
readinessProbe:
  httpGet:
    path: /api/health/
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5

livenessProbe:
  httpGet:
    path: /api/health/
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
```

- **readinessProbe:** K8s no manda tráfico hasta que el pod responda 200
- **livenessProbe:** K8s reinicia el pod si deja de responder

Sin estas probes, los usuarios ven errores 502 durante los deploys.

### Tarea 3 · Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: django-api-hpa
spec:
  scaleTargetRef:
    name: django-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

Prueba la resiliencia eliminando pods manualmente: `kubectl delete pod django-api-xxx`. Kubernetes debe recrearlos automáticamente.

---

## Fase 8 — Observabilidad
**Semanas 17 a 18 · Prometheus + Grafana**

### Objetivo
Ver en tiempo real qué está pasando dentro del sistema: latencia, errores, usuarios activos, estado de Kafka.

### Tarea 1 · Exportar métricas desde Django

```python
# Instalar: django-prometheus
INSTALLED_APPS += ["django_prometheus"]
MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    ...
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]
```

Prometheus scrapea `/metrics` cada 15 segundos. Métricas disponibles automáticamente: requests por segundo, latencia por endpoint, errores 4xx/5xx, queries a DB.

**Métricas custom a añadir:**

```python
from prometheus_client import Gauge, Counter

ACTIVE_TOURNAMENTS = Gauge('active_tournaments_total',
                           'Torneos activos ahora')
MATCHES_REPORTED   = Counter('matches_reported_total',
                             'Total de partidas reportadas')
```

### Tarea 2 · Dashboards en Grafana

| Dashboard | Paneles |
|---|---|
| **API Health** | RPS, latencia p50/p95/p99, tasa de errores |
| **Plataforma** | Usuarios registrados hoy, torneos activos, partidas jugadas |
| **Kafka** | Lag por consumer group — si sube indefinidamente, hay un consumer roto |

**Alerta crítica a configurar:** si la tasa de error supera el 5% durante 5 minutos consecutivos, enviar notificación al equipo.

El lag de Kafka es la métrica más importante de los consumers. Un lag creciente indica que el consumer no procesa eventos a la velocidad que se producen.

---

## Estructura del proyecto

```
tournament-platform/
├── services/
│   ├── django-api/          # Backend principal
│   ├── java-auth/           # Microservicio de autenticación
│   └── notification-service/
├── infrastructure/
│   ├── docker/
│   │   ├── docker-compose.yml
│   │   └── .env.example
│   ├── kubernetes/
│   │   ├── base/
│   │   └── overlays/
│   └── monitoring/          # Prometheus + Grafana
├── docs/
│   ├── architecture.md
│   └── adr/                 # Architecture Decision Records
├── scripts/
│   ├── setup.sh
│   └── seed.py
├── Makefile
└── README.md
```

---

## Comandos rápidos

```bash
# Levantar el stack completo
make dev

# Correr todos los tests
make test

# Aplicar migraciones
make migrate

# Generar datos de prueba
make seed

# Ver logs en tiempo real
make logs
```

---

*Duración estimada: 18 semanas trabajando de forma constante.*
*Cada fase construye sobre la anterior — no saltes fases.*