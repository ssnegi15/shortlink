# ShortLink

Production-oriented URL shortener using ASP.NET Core and .NET 10.

## Endpoints

`POST /admin/links` creates a short link.

`GET /{code}` returns HTTP 302 for an active link and HTTP 404 when missing.

HTTP 429 is returned when the distributed rate limiter rejects the request.

## Architecture

```text
GET /code
   |
   v
Redis distributed rate limiter
   |
   v
HybridCache
   |
   +-- L1 memory HIT -----> 302
   |
   +-- L2 Redis HIT ------> 302
   |
   +-- MISS
        |
        v
     EF Core
        |
        v
    PostgreSQL HA
       /      \
    found    missing
      |          |
      v          v
   cache 24h   cache 15s
      |          |
      +----+-----+
           |
           v
        302/404
```

## Caching

- HybridCache L1: process memory.
- HybridCache L2: Redis.
- Positive cache lifetime: 24 hours.
- Negative Redis cache lifetime: 15 seconds.

## PostgreSQL HA

Npgsql uses transient failure retries. Production deployments should use a PostgreSQL HA or managed endpoint.

## Redis

Redis is used for HybridCache L2, negative caching, and distributed rate limiting.

The Redis connection is supplied through configuration, so a Redis HA/Cluster deployment can be used in production.

## Rate limiting

Rate limiting is Redis-backed so multiple API instances share the same rate-limit state.

For internet-facing production systems, an API gateway or edge limiter should also be used.

## Health and metrics

- `/health/live` - liveness.
- `/health/ready` - PostgreSQL and Redis readiness.
- `/metrics` - Prometheus metrics.

## Local development

```bash
docker compose up --build
```

API: `http://localhost:8080`

Prometheus: `http://localhost:9090`

Grafana: `http://localhost:3000`

## k6

The supplied load test models a 5,000 RPS peak for two minutes.

```bash
k6 run -e BASE_URL=http://localhost:8080 -e CODE=aZ91kLm2Pq7X loadtest/redirect.js
```

## EF migrations

The bootstrap GitHub Actions workflow generates EF Core migrations before building and testing.

## Production checklist

- Protect `/admin/links` with authentication and authorization.
- Use TLS.
- Configure trusted proxy headers.
- Use PostgreSQL HA.
- Use Redis HA or Redis Cluster.
- Protect `/metrics`.
- Configure secrets outside source control.
- Configure connection pools for the deployment size.
- Monitor PostgreSQL, Redis, latency, errors, cache behavior, and rate limiting.
