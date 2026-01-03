# What to Watch Next – Backend

Spring Boot backend for the *What to Watch Next* project.

## Tech Stack

- Java 21
- Spring Boot 3.2
- Spring Data JPA (Hibernate)
- PostgreSQL (Neon) + pgvector
- Maven
- 
## Architecture

This project is part of a larger system split into multiple components.

### Offline data pipeline (Python)
Responsible for fetching metadata, computing embeddings, and storing
the data in PostgreSQL (Neon).

→ Repository: https://github.com/dmolinsky/what-to-watch-next-pipeline

### Backend API (Spring Boot)
This repository.

- Exposes a REST API for searching titles and fetching recommendations
- Performs on-demand vector similarity search using pgvector
- Applies ranking and filtering logic
- Caches expensive recommendation queries to reduce database load

### Frontend (planned)
A React + TypeScript frontend that consumes the backend API and presents
search results and recommendations.

## Recommendation Engine

Recommendations are computed on demand using vector similarity search
with pgvector. Each request compares a title’s combined embedding
against all other embeddings in the database.

To improve performance and reduce database load, recommendation results
are cached per title and limit.

## Configuration

The application expects the following environment variables:

- `DATABASE_URL` – JDBC connection string to PostgreSQL

## API Endpoints

- `GET /api/health`
- `GET /api/titles/{id}`
- `GET /api/titles/{id}/recommendations?limit=5`

## Why this project?

This project was built to explore modern backend patterns such as
vector databases, similarity search, and caching, while maintaining
clean architecture and production-ready design.