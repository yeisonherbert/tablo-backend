# Tablo — Backend

Clon de Trello construido con **FastAPI**, **SQLAlchemy (async)**, **Strawberry GraphQL** y **PostgreSQL**.
Autenticación con Google OAuth + JWT propio.

- API REST: `POST /auth/google` (login)
- API GraphQL: `POST /graphql` (queries y mutations)
- Health check: `GET /health`

---

## Tabla de contenidos

1. [Requisitos previos](#requisitos-previos)
2. [Variables de entorno](#variables-de-entorno)
3. [Levantar en local](#levantar-en-local)
   - [macOS](#macos)
   - [Linux](#linux)
   - [Windows](#windows)
4. [Levantar con Docker](#levantar-con-docker)
5. [Desplegar en AWS](#desplegar-en-aws)
   - [Opción A — ECS Fargate (recomendada)](#opcion-a--ecs-fargate-recomendada)
   - [Opción B — EC2 + Docker](#opcion-b--ec2--docker)
   - [Opción C — App Runner](#opcion-c--app-runner)
6. [Probar la API](#probar-la-api)
7. [Estructura del proyecto](#estructura-del-proyecto)

---

## Requisitos previos

- **Python 3.12+**
- **PostgreSQL 16+** accesible (en este proyecto se usa una instancia RDS PostgreSQL 18.3 ya provisionada)
- **Docker 24+** y **Docker Compose v2** (sólo para la ruta Docker)
- **Google Cloud Console** — un OAuth 2.0 Client ID si vas a verificar tokens reales

Las tablas (`users`, `projects`, `project_collaborators`, `tasks`) y el tipo enum `task_status_enum` deben existir en la base de datos antes de arrancar la app — este backend **no las crea**.

---

## Variables de entorno

Copia el archivo de ejemplo y ajústalo:

```bash
cp .env.example .env
```

Variables principales:

| Variable             | Descripción                                                | Por defecto                                                       |
|----------------------|------------------------------------------------------------|-------------------------------------------------------------------|
| `DB_HOST`            | Host del PostgreSQL                                        | `postgres-dev.cb4oayqkid8w.us-east-2.rds.amazonaws.com`           |
| `DB_PORT`            | Puerto                                                     | `5432`                                                            |
| `DB_USER`            | Usuario                                                    | `postgresql`                                                      |
| `DB_PASSWORD`        | Password                                                   | `pass123`                                                         |
| `DB_NAME`            | Nombre de la base de datos                                 | `tablo`                                                           |
| `JWT_SECRET`         | Secreto para firmar el JWT (genera con `openssl rand -hex 32`) | `change-me-in-production`                                     |
| `JWT_ALGORITHM`      | Algoritmo                                                  | `HS256`                                                           |
| `JWT_EXPIRE_MINUTES` | Tiempo de vida del JWT en minutos                          | `1440` (24h)                                                      |
| `GOOGLE_CLIENT_ID`   | OAuth Client ID de Google (vacío = no valida audiencia)    | *(vacío)*                                                         |

> En producción **siempre** rota `JWT_SECRET` y define `GOOGLE_CLIENT_ID`. Guarda el secreto en AWS Secrets Manager o SSM Parameter Store, no en `.env`.

---

## Levantar en local

### macOS

```bash
# 1. Instalar Python (si no lo tienes)
brew install python@3.12

# 2. Clonar y entrar al proyecto
cd /Users/$USER/tablo

# 3. Crear entorno virtual
python3.12 -m venv .venv
source .venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Configurar variables
cp .env.example .env
# edita .env con tu editor

# 6. Arrancar
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Si `pip install` falla por `cryptography` o `asyncpg`, instala las cabeceras:

```bash
brew install openssl libpq
export LDFLAGS="-L$(brew --prefix openssl)/lib -L$(brew --prefix libpq)/lib"
export CPPFLAGS="-I$(brew --prefix openssl)/include -I$(brew --prefix libpq)/include"
```

### Linux

#### Debian / Ubuntu

```bash
# 1. Dependencias del sistema
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3-pip build-essential libpq-dev

# 2. Clonar el proyecto y entrar
cd ~/tablo

# 3. Entorno virtual e instalación
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Configurar y correr
cp .env.example .env
nano .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Fedora / RHEL

```bash
sudo dnf install -y python3.12 python3-pip gcc postgresql-devel
# ... resto igual que Debian
```

#### Arch

```bash
sudo pacman -S python python-pip postgresql-libs base-devel
# ... resto igual
```

### Windows

Hay dos rutas: **PowerShell nativo** o **WSL2** (recomendado si vienes de Linux).

#### Opción 1 — PowerShell

```powershell
# 1. Instalar Python 3.12 desde https://www.python.org/downloads/windows/
#    (marca "Add Python to PATH" durante el instalador)

# 2. Verificar
python --version

# 3. Clonar y entrar al proyecto
cd C:\Users\<tu-usuario>\tablo

# 4. Entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Si PowerShell bloquea la activación:
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# 5. Instalar dependencias
pip install -r requirements.txt

# 6. Configurar variables (copiar y editar)
Copy-Item .env.example .env
notepad .env

# 7. Arrancar
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> Si `pip install cryptography` falla, instala **Microsoft C++ Build Tools** desde https://visualstudio.microsoft.com/visual-cpp-build-tools/.

#### Opción 2 — WSL2 (recomendado)

```powershell
wsl --install -d Ubuntu
```

Luego dentro de WSL sigue las instrucciones de [Linux / Debian](#debian--ubuntu).

---

## Levantar con Docker

Funciona igual en macOS, Linux y Windows (con Docker Desktop o Docker Engine).

```bash
# 1. Configurar variables
cp .env.example .env
# edita .env

# 2. Build + run
docker compose up --build

# En background
docker compose up -d --build

# Ver logs
docker compose logs -f api

# Parar
docker compose down
```

La API queda en **http://localhost:8000**.

Para reconstruir desde cero:

```bash
docker compose down -v
docker compose build --no-cache
docker compose up
```

---

## Desplegar en AWS

A continuación tres rutas, ordenadas de más a menos recomendada para una app como esta.

### Opción A — ECS Fargate (recomendada)

Mantiene la app en contenedores gestionados, sin servidores que parchear, con autoscaling y rolling deploys.

#### Arquitectura

```
Internet ─▶ ALB (HTTPS) ─▶ ECS Fargate Service ─▶ RDS PostgreSQL
                                  │
                                  ├─ Secrets Manager (JWT_SECRET, DB_PASSWORD)
                                  └─ CloudWatch Logs
```

#### Paso 1 — Subir la imagen a ECR

```bash
# Variables
AWS_REGION=us-east-2
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REPO=tablo-api

# Crear repositorio
aws ecr create-repository --repository-name $REPO --region $AWS_REGION

# Login docker → ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build y push
docker build -t $REPO .
docker tag $REPO:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO:latest
```

> En Apple Silicon (M1/M2/M3), agrega `--platform linux/amd64` al `docker build` si tu servicio ECS corre en x86, o usa arquitectura `ARM64` en la task definition.

#### Paso 2 — Guardar secretos en Secrets Manager

```bash
aws secretsmanager create-secret --name tablo/jwt_secret \
  --secret-string "$(openssl rand -hex 32)"

aws secretsmanager create-secret --name tablo/db_password \
  --secret-string "pass123"
```

#### Paso 3 — Crear el clúster ECS y la task definition

```bash
aws ecs create-cluster --cluster-name tablo-cluster --region $AWS_REGION
```

`task-definition.json` (ajusta cuentas y ARNs):

```json
{
  "family": "tablo-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::<ACCOUNT_ID>:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "<ACCOUNT_ID>.dkr.ecr.us-east-2.amazonaws.com/tablo-api:latest",
      "essential": true,
      "portMappings": [{ "containerPort": 8000, "protocol": "tcp" }],
      "environment": [
        { "name": "DB_HOST",    "value": "postgres-dev.cb4oayqkid8w.us-east-2.rds.amazonaws.com" },
        { "name": "DB_PORT",    "value": "5432" },
        { "name": "DB_USER",    "value": "postgresql" },
        { "name": "DB_NAME",    "value": "tablo" },
        { "name": "GOOGLE_CLIENT_ID", "value": "<tu-client-id>.apps.googleusercontent.com" }
      ],
      "secrets": [
        { "name": "JWT_SECRET",  "valueFrom": "arn:aws:secretsmanager:us-east-2:<ACCOUNT_ID>:secret:tablo/jwt_secret"  },
        { "name": "DB_PASSWORD", "valueFrom": "arn:aws:secretsmanager:us-east-2:<ACCOUNT_ID>:secret:tablo/db_password" }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/tablo-api",
          "awslogs-region": "us-east-2",
          "awslogs-stream-prefix": "ecs",
          "awslogs-create-group": "true"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

Registra:

```bash
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

#### Paso 4 — ALB y servicio ECS

Crea por consola:

1. **Target Group**: tipo `IP`, protocolo `HTTP`, puerto `8000`, health check path `/health`.
2. **Application Load Balancer**: en subnets públicas, listener `:443` con certificado ACM, default action → target group de arriba.
3. **ECS Service**:
   - Cluster: `tablo-cluster`
   - Launch type: `FARGATE`
   - Task definition: `tablo-api`
   - Desired tasks: 2
   - Subnets: privadas (sin IP pública)
   - Security group: permite `:8000` desde el SG del ALB
   - Load balancer: el ALB y target group creados

> El **security group del RDS** debe permitir `:5432` desde el SG del ECS service.

#### Paso 5 — DNS y CI/CD

- **Route 53**: registro A (alias) → ALB DNS.
- **CI/CD**: pipeline simple (GitHub Actions) que en cada push a `main` haga `docker build`, push a ECR y `aws ecs update-service --force-new-deployment`. ECS hace rolling deploy sin downtime.

---

### Opción B — EC2 + Docker

Más barata y simple; útil para staging o demos.

```bash
# 1. Lanzar una EC2 t3.small con Amazon Linux 2023
#    Security Group: permitir 22 (tu IP), 80 y 443 (0.0.0.0/0)

# 2. SSH y preparar
ssh ec2-user@<EC2_PUBLIC_IP>
sudo dnf update -y
sudo dnf install -y docker git
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user
exit && ssh ec2-user@<EC2_PUBLIC_IP>  # re-login para tomar el grupo

# 3. Instalar docker compose plugin
DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
mkdir -p $DOCKER_CONFIG/cli-plugins
curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
  -o $DOCKER_CONFIG/cli-plugins/docker-compose
chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose

# 4. Clonar y configurar
git clone <tu-repo> tablo && cd tablo
cp .env.example .env
nano .env

# 5. Arrancar
docker compose up -d --build

# 6. (Opcional) Nginx + Certbot delante para HTTPS
sudo dnf install -y nginx certbot python3-certbot-nginx
# configura /etc/nginx/conf.d/tablo.conf como reverse proxy a localhost:8000
sudo certbot --nginx -d api.tudominio.com
```

> Asegúrate de que el SG del RDS permita conexiones desde el SG de la EC2.

---

### Opción C — App Runner

La más rápida si no necesitas configurar red avanzada. App Runner toma una imagen de ECR (o un repo de GitHub) y la sirve detrás de HTTPS gestionado.

```bash
# 1. Sube la imagen a ECR (igual que Opción A, Paso 1)

# 2. Crea el servicio
aws apprunner create-service \
  --service-name tablo-api \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "<ACCOUNT_ID>.dkr.ecr.us-east-2.amazonaws.com/tablo-api:latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          "DB_HOST": "postgres-dev.cb4oayqkid8w.us-east-2.rds.amazonaws.com",
          "DB_PORT": "5432",
          "DB_USER": "postgresql",
          "DB_NAME": "tablo"
        },
        "RuntimeEnvironmentSecrets": {
          "JWT_SECRET":  "arn:aws:secretsmanager:us-east-2:<ACCOUNT_ID>:secret:tablo/jwt_secret",
          "DB_PASSWORD": "arn:aws:secretsmanager:us-east-2:<ACCOUNT_ID>:secret:tablo/db_password"
        }
      }
    },
    "AutoDeploymentsEnabled": true
  }' \
  --health-check-configuration '{
    "Protocol": "HTTP",
    "Path": "/health",
    "Interval": 10,
    "Timeout": 5,
    "HealthyThreshold": 2,
    "UnhealthyThreshold": 3
  }' \
  --instance-configuration '{
    "Cpu": "1024",
    "Memory": "2048"
  }'
```

Para acceder al RDS desde App Runner crea un **VPC Connector** que apunte a las subnets privadas donde vive el RDS y asocialo al servicio.

---

## Probar la API

### 1) Login (REST)

```bash
curl -X POST http://localhost:8000/auth/google \
  -H "Content-Type: application/json" \
  -d '{"id_token": "<ID_TOKEN_DE_GOOGLE>"}'
```

Respuesta:

```json
{ "access_token": "eyJ...", "token_type": "bearer" }
```

### 2) GraphQL

Abre el playground en http://localhost:8000/graphql y añade el header:

```
Authorization: Bearer eyJ...
```

#### Crear un proyecto

```graphql
mutation {
  createProject(name: "Mi tablero", description: "Sprint 1") {
    id
    name
    createdAt
  }
}
```

#### Añadir colaborador por email

```graphql
mutation {
  addCollaborator(projectId: "<UUID>", email: "amigo@mail.com") {
    id
    collaborators { id email }
  }
}
```

#### Crear tarea (entra en `backlog`)

```graphql
mutation {
  createTask(projectId: "<UUID>", title: "Diseñar login") {
    id
    status
  }
}
```

#### Mover tarea entre columnas

```graphql
mutation {
  moveTask(taskId: "<UUID>", newStatus: IN_PROGRESS) {
    id
    title
    status
    updatedAt
  }
}
```

#### Ver un proyecto con tareas ordenadas por columna

```graphql
query {
  project(projectId: "<UUID>") {
    name
    owner { name email }
    collaborators { name email }
    tasks { id title status assigneeId }
  }
}
```

---

## Estructura del proyecto

```
tablo/
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── requirements.txt
├── README.md
└── app/
    ├── main.py              FastAPI entry; monta REST y /graphql
    ├── config.py            Settings (pydantic-settings + .env)
    ├── database.py          Engine async + sessionmaker + get_session
    ├── models/
    │   ├── user.py          SQLAlchemy User
    │   ├── project.py       Project + tabla pivote project_collaborators
    │   └── task.py          Task + enum TaskStatus
    ├── auth/
    │   ├── google.py        verify_google_token (google-auth)
    │   ├── jwt_handler.py   create / decode / extract con python-jose
    │   ├── router.py        POST /auth/google → JWT
    │   └── dependencies.py  get_current_user, get_optional_user
    └── graphql/
        ├── schema.py        strawberry.Schema(query, mutation)
        ├── context.py       Context inyectado vía Depends
        ├── permissions.py   IsAuthenticated
        ├── queries.py       me, myProjects, project(id)
        ├── mutations.py     createProject, addCollaborator, createTask, moveTask
        └── types/           UserType, ProjectType, TaskType + enum
```
