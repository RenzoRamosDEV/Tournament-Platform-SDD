## ADDED Requirements

### Requirement: Nginx es el único servicio con puerto publicado al host
El servicio `nginx` SHALL ser el único servicio que publica un puerto al host (`80:80`). El resto de servicios SHALL exponer sus puertos únicamente en la red interna `app-network`.

#### Scenario: Solo el puerto 80 accesible desde el host
- **WHEN** se ejecuta `docker compose ps` con el stack corriendo
- **THEN** solo el servicio `nginx` muestra un mapeo de puertos con `0.0.0.0:80`

---

### Requirement: Nginx proxea /api/* a django-api stripeando el prefijo
`nginx.conf` SHALL redirigir las peticiones con prefijo `/api/` a `http://django-api:8000/`, stripeando el prefijo `/api` antes de proxear.

#### Scenario: Petición a /api/tournaments/ llega a django-api como /tournaments/
- **WHEN** se hace `curl http://localhost/api/tournaments/`
- **THEN** nginx proxea a `django-api:8000/tournaments/` y retorna HTTP 200 o 401 (no 502 ni 404)

---

### Requirement: Nginx proxea /auth/* a java-auth stripeando el prefijo
`nginx.conf` SHALL redirigir las peticiones con prefijo `/auth/` a `http://java-auth:8080/`, stripeando el prefijo `/auth` antes de proxear.

#### Scenario: Petición a /auth/login llega a java-auth como /auth/login
- **WHEN** se hace `curl -X POST http://localhost/auth/login` con body JSON
- **THEN** nginx proxea a `java-auth:8080/auth/login` y retorna HTTP 200 o 401 (no 502)

---

### Requirement: Nginx retorna 404 para rutas no reconocidas
Las peticiones que no tengan prefijo `/api/` ni `/auth/` SHALL recibir respuesta HTTP 404 de nginx.

#### Scenario: Ruta desconocida retorna 404
- **WHEN** se hace `curl http://localhost/unknown-path`
- **THEN** la respuesta tiene código HTTP 404

---

### Requirement: nginx.conf montado desde ./nginx/nginx.conf
El servicio `nginx` SHALL montar el archivo `./nginx/nginx.conf` del host como `/etc/nginx/nginx.conf` en el contenedor.

#### Scenario: Cambio en nginx.conf se aplica tras recrear el contenedor
- **WHEN** se modifica `./nginx/nginx.conf` y se ejecuta `docker compose up -d --force-recreate nginx`
- **THEN** nginx aplica la nueva configuración

---

### Requirement: nginx depende de django-api y java-auth iniciados
El servicio `nginx` SHALL declarar `depends_on` con `condition: service_started` para `django-api` y `java-auth`.

#### Scenario: nginx arranca después de los servicios backend
- **WHEN** se ejecuta `docker compose up -d`
- **THEN** el contenedor nginx no inicia hasta que los contenedores django-api y java-auth han sido creados
