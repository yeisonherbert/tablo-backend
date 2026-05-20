# Tablo — Backend (API REST)

API REST para **Tablo**, un clon de Trello. Construida con **FastAPI** + **SQLAlchemy 2.0 (async)** sobre **PostgreSQL 18**, con autenticación simulada vía **Email + JWT** (sin contraseñas).

---

## Stack

- Python 3.13
- FastAPI · Starlette · Uvicorn
- SQLAlchemy 2.0 (async) + asyncpg
- Pydantic v2 / pydantic-settings
- python-jose (JWT HS256)

---

## Estructura del proyecto

```
backend/
├── app/
│   ├── main.py              # App FastAPI, CORS, routers y /health
│   ├── config.py            # Settings (env/.env): BD y JWT
│   ├── database.py          # Engine async, sesión y Base declarativa
│   ├── models/              # Modelos ORM (SQLAlchemy)
│   │   ├── user.py
│   │   ├── project.py       # Project + tabla pivote project_members
│   │   └── task.py          # Task + ENUM task_status
│   ├── schemas/             # Esquemas Pydantic (entrada/salida)
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── project.py
│   │   └── task.py
│   ├── auth/
│   │   ├── jwt_handler.py    # Crear/validar JWT
│   │   └── dependencies.py   # get_current_user (Depends de protección)
│   └── routers/
│       ├── auth.py           # POST /auth/login
│       ├── projects.py       # CRUD de proyectos, miembros y tareas
│       └── tasks.py          # PATCH /tasks/{id}
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

> **Nota:** las tablas (`users`, `projects`, `project_members`, `tasks`) y el tipo
> `task_status` ya existen en la base de datos. La app **no** ejecuta migraciones;
> solo se conecta y opera sobre el esquema existente.

---

## Endpoints

| Método | Ruta                            | Descripción                                            | Auth |
|--------|---------------------------------|--------------------------------------------------------|:----:|
| POST   | `/auth/login`                   | Login con correo `@gmail.com`; crea el usuario si no existe y devuelve un JWT | ❌ |
| POST   | `/projects`                     | Crear un proyecto                                      | ✅ |
| GET    | `/projects`                     | Listar los proyectos del usuario logueado              | ✅ |
| GET    | `/projects/{project_id}`        | Detalle: participantes + tareas ordenadas por estado   | ✅ |
| POST   | `/projects/{project_id}/members`| Añadir un participante por email                       | ✅ |
| POST   | `/projects/{project_id}/tasks`  | Crear una tarea (nace en `backlog`)                    | ✅ |
| PATCH  | `/tasks/{task_id}`              | Actualizar el estado de una tarea                      | ✅ |
| GET    | `/health`                       | Health check                                           | ❌ |

Estados de tarea: `backlog` → `to_do` → `in_progress` → `completed`.

Documentación interactiva una vez levantado:
- Swagger UI → http://localhost:8000/docs
- ReDoc → http://localhost:8000/redoc

### Autenticación

El login devuelve `access_token`. Envíalo en cada petición protegida:

```
Authorization: Bearer <access_token>
```

---

## Configuración (variables de entorno)

Copia `.env.example` a `.env` y ajusta los valores:

```bash
cp .env.example .env
```

| Variable             | Descripción                          |
|----------------------|--------------------------------------|
| `DB_HOST`            | Host de PostgreSQL                   |
| `DB_PORT`            | Puerto (5432)                        |
| `DB_USER`            | Usuario                              |
| `DB_PASSWORD`        | Contraseña                           |
| `DB_NAME`            | Nombre de la base                    |
| `DB_ECHO`            | `true` para loguear el SQL           |
| `JWT_SECRET`         | Secreto para firmar los JWT          |
| `JWT_ALGORITHM`      | Algoritmo (por defecto `HS256`)      |
| `JWT_EXPIRE_MINUTES` | Vigencia del token en minutos        |

> Genera un secreto seguro:
> `python -c "import secrets; print(secrets.token_urlsafe(48))"`

---

## Cómo levantar en local

### Linux / macOS

```bash
cd backend

# 1. Crear y activar el entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env        # edita .env si hace falta

# 4. Levantar el servidor (con auto-reload en desarrollo)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Windows (PowerShell)

```powershell
cd backend

# 1. Crear y activar el entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
Copy-Item .env.example .env   # edita .env si hace falta

# 4. Levantar el servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> Si PowerShell bloquea la activación del venv, ejecuta una vez:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

### Windows (CMD)

```bat
cd backend
python -m venv .venv
.\.venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La API quedará disponible en http://localhost:8000 (docs en `/docs`).

---

## Cómo levantar con Docker

Requiere Docker y Docker Compose. Asegúrate de tener tu archivo `.env` listo.

### Con Docker Compose (recomendado)

```bash
cd backend
cp .env.example .env          # en Windows: copy .env.example .env
docker compose up --build
```

### Con Docker a secas

```bash
cd backend
docker build -t tablo-api .
docker run --rm -p 8000:8000 --env-file .env tablo-api
```

La API quedará en http://localhost:8000.

> La base de datos es un PostgreSQL gestionado (AWS RDS), por lo que el
> contenedor solo expone la API y se conecta a la BD remota usando el `.env`.

---

## Prueba rápida (curl)

```bash
# 1. Login (devuelve el token)
curl -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"ada.lovelace@gmail.com"}'

# 2. Crear proyecto (usa el token del paso anterior)
TOKEN=<pega-tu-token>
curl -X POST http://localhost:8000/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Sprint 1","description":"Primer tablero"}'

# 3. Crear tarea
curl -X POST http://localhost:8000/projects/<PROJECT_ID>/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"title":"Diseñar el esquema"}'

# 4. Mover la tarea de columna
curl -X PATCH http://localhost:8000/tasks/<TASK_ID> \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"status":"in_progress"}'
```
