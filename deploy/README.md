# Deployment

This directory contains deployment configuration files for the AfterIDE project.

## Files

- **docker-compose.yml** - Docker Compose configuration for running the entire AfterIDE stack

## Usage

### Running with Docker Compose
```bash
cd deploy
docker-compose up -d
```

### Stopping the Stack
```bash
cd deploy
docker-compose down
```

## Notes

This configuration allows you to run the entire AfterIDE application stack in containers, including the backend API, frontend, and database services. 