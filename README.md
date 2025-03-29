# FastAPI Application with MySQL

This project uses FastAPI with MySQL database and Docker for containerization.

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Poetry 1.x.x (for dependency management)
- MySQL client (optional, for database management)

## Project Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd <project-directory>
```

2. Install dependencies using Poetry:

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Activate the virtual environment
poetry shell
```

## Running the Application

### Local Development (Without Docker)

1. Start MySQL database using Docker:

```bash
docker-compose up -d mysql
```

2. Run database migrations:

```bash
# Make sure you're in the Poetry shell
poetry shell

# Run migrations
poetry run alembic upgrade head
```

3. Start the application:

```bash
# Make sure you're in the Poetry shell
poetry shell

# Run the application with auto-reload
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at `http://localhost:8000`

### Docker Deployment

### Step 1: Start MySQL Database

First, start only the MySQL container:

```bash
docker-compose up -d mysql
```

### Step 2: Run Database Migrations

Before starting the application, you need to run the database migrations. You can do this in two ways:

#### Option 1: Run migrations locally (recommended for development)

```bash
# Make sure you're in the Poetry shell
poetry shell

# Run migrations
poetry run alembic upgrade head
```

#### Option 2: Run migrations inside Docker container

```bash
# Start a temporary container with the application
docker-compose run --rm app alembic upgrade head
```

### Step 3: Start the Application

After migrations are complete, start the full application stack:

```bash
docker-compose up -d
```

The application will be available at `http://localhost:8000`

## Development Workflow

### Creating New Migrations

When you make changes to your models, create a new migration:

```bash
# Make sure you're in the Poetry shell
poetry shell

# Create a new migration
poetry run alembic revision --autogenerate -m "description of changes"

# Apply the new migration
poetry run alembic upgrade head
```

### Stopping the Application

To stop the application:

```bash
docker-compose down
```

To stop the application and remove the database volume:

```bash
docker-compose down -v
```

## Environment Variables

The application uses the following environment variables:

- `DB_USER`: Database username (default: root)
- `DB_PASSWORD`: Database password (default: Gcort_50)
- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 3306)
- `DB_NAME`: Database name (default: FastAPI_TEST)

These variables can be overridden by creating a `.env` file in the project root.

## Troubleshooting

1. If you can't connect to the database:

   - Make sure MySQL container is running: `docker-compose ps`
   - Check MySQL logs: `docker-compose logs mysql`
   - Verify database credentials in your `.env` file

2. If migrations fail:

   - Make sure MySQL is running and accessible
   - Check if the database exists: `docker-compose exec mysql mysql -u root -p -e "SHOW DATABASES;"`
   - Verify your models are properly imported in `alembic/env.py`

3. If the application fails to start:
   - Check application logs: `docker-compose logs app`
   - Verify all environment variables are set correctly
   - Ensure all migrations are applied

## Poetry Commands Reference

Here are some useful Poetry commands for development:

```bash
# Add a new dependency
poetry add package-name

# Add a development dependency
poetry add --group dev package-name

# Update dependencies
poetry update

# Show installed packages
poetry show

# Export requirements.txt (if needed)
poetry export -f requirements.txt --output requirements.txt --without-hashes
```
