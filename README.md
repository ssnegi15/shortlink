# ShortLink

ShortLink is a small, production-oriented URL shortener built with ASP.NET Core, PostgreSQL, Redis, and .NET 10. Redirects are cached with `HybridCache`, rate limits are shared through Redis, and the service exposes health and Prometheus endpoints.

## Run locally

Requirements:

- Docker Desktop with Compose
- .NET 10 SDK for local builds and tests

Start the complete local stack:

```bash
cp .env.example .env
docker compose up --build
```

The API applies the checked-in EF migration automatically when running in the Compose `Development` environment. Compose services bind to localhost. Services are available at:

| Service    | URL                   |
| ---------- | --------------------- |
| API        | http://localhost:8080 |
| Prometheus | http://localhost:9090 |
| Grafana    | http://localhost:3000 |

Stop the stack with `docker compose down`. Add `-v` only when you want to delete the local PostgreSQL, Redis, and Grafana data volumes.

## API

Create a link with the configured admin key. The endpoint is protected in both local and hosted environments.

```bash
curl -i -X POST http://localhost:8080/admin/links \
  -H "X-Admin-Key: ${SHORTLINK_ADMIN_API_KEY:-local-development-only}" \
  -H 'Content-Type: application/json' \
  -d '{"destinationUrl":"https://example.com/docs","code":"docs"}'
```

Optional `expiresAt` values must be future UTC timestamps:

```json
{
  "destinationUrl": "https://example.com/campaign",
  "expiresAt": "2027-01-01T00:00:00Z"
}
```

Resolve a link:

```bash
curl -i http://localhost:8080/docs
```

An active link returns `302`; an unknown, inactive, or expired link returns `404`. Redirect requests can return `429` when the Redis-backed per-client limit is exceeded.

## Architecture

See the full [architecture guide](docs/ARCHITECTURE.md) for request-flow diagrams, cache and rate-limit behavior, deployment topology, failure handling, security boundaries, and design tradeoffs.

```text
Client -> ASP.NET Core -> Redis rate limiter -> HybridCache -> PostgreSQL
                                      |             |
                                      +-------------+--> 302 or 404
```

- PostgreSQL stores link records and enforces unique short codes.
- Redis provides the distributed rate limiter, HybridCache L2 storage, and short-lived negative lookup caching.
- HybridCache keeps successful lookups in process memory and Redis. Cached values retain `ExpiresAt`, so an expired link cannot redirect even if its cache entry has not reached its maximum lifetime.
- `/health/live` checks process liveness. `/health/ready` checks PostgreSQL and Redis connectivity.
- `/metrics` exposes Prometheus metrics. Protect it when deployed outside a trusted network.

## Configuration

Configuration uses standard ASP.NET Core keys. Environment variables use double underscores, for example `ConnectionStrings__Postgres`.

| Key                             | Default                 | Purpose                                                           |
| ------------------------------- | ----------------------- | ----------------------------------------------------------------- |
| `ConnectionStrings:Postgres`    | `localhost` connection  | PostgreSQL connection string                                      |
| `Redis:Configuration`           | `localhost:6379`        | Redis endpoint or cluster configuration                           |
| `RateLimiting:PermitLimit`      | `120`                   | Requests per client window                                        |
| `RateLimiting:WindowSeconds`    | `1`                     | Rate-limit window size                                            |
| `RateLimiting:FailOpen`         | `false`                 | Whether requests are allowed if Redis is unavailable              |
| `ShortLink:CodeLength`          | `12`                    | Generated code length                                             |
| `ShortLink:BaseUrl`             | `http://localhost:8080` | Base URL returned by link creation                                |
| `ShortLink:AdminApiKey`         | required                | API key for `/admin/links`                                        |
| `ForwardedHeaders:KnownProxies` | empty                   | IPs allowed to supply `X-Forwarded-*` headers                     |
| `ForwardedHeaders:TrustAll`     | `false`                 | Trust one proxy hop when the hosting platform hides its proxy IPs |
| `Database:ApplyMigrations`      | `false`                 | Apply EF migrations during startup                                |
| `Metrics:Enabled`               | `true`                  | Expose the Prometheus `/metrics` endpoint                         |

The admin endpoint returns `503` when no API key is configured and rejects requests without the `X-Admin-Key` header. Supply the key through a deployment secret, never source control. Forwarded headers are ignored unless the sender's IP is listed in `ForwardedHeaders:KnownProxies`.

For local Compose, `.env` supplies development-only values. It is ignored by Git and must never contain production credentials.

## Development commands

```bash
dotnet restore ShortLink.sln
dotnet build ShortLink.sln
dotnet test ShortLink.sln
```

GitHub Actions runs the same restore, build, and test steps for pushes to `main` and pull requests.

To create a migration after changing the EF model:

```bash
dotnet ef migrations add NameOfChange \
  --project src/ShortLink.Api \
  --startup-project src/ShortLink.Api
```

The benchmark project contains a redirect-load benchmark. The supplied k6 script models a 5,000 RPS peak for two minutes:

```bash
k6 run -e BASE_URL=http://localhost:8080 -e CODE=docs loadtest/redirect.js
```

## Production checklist

- Set a strong secret for `ShortLink:AdminApiKey` and rotate it through the hosting provider's secret manager.
- Run migrations as a controlled deployment step. The Render blueprint enables startup migrations for its single free instance; disable this for larger production deployments and run `dotnet ef database update` separately.
- Use TLS and configure `ForwardedHeaders:KnownProxies` for the actual reverse proxy addresses.
- Use managed or highly available PostgreSQL and Redis.
- Protect `/metrics`, Grafana, and Prometheus.
- Do not expose PostgreSQL, Redis, Prometheus, or Grafana publicly.
- Configure backups and restore drills for PostgreSQL.
- Set connection pool sizes and rate limits for the deployment capacity.
- Monitor redirect latency, 404/429 rates, cache behavior, and PostgreSQL/Redis health.

## Hosting

GitHub Pages can host a static frontend or this documentation, but it cannot run this ASP.NET Core API, PostgreSQL, or Redis. Deploy the API to a container-capable provider and use managed database services. Free tiers change frequently, so verify current quotas, sleep behavior, bandwidth, and database retention before choosing a provider.

### Render deployment

The checked-in `render.yaml` creates a free Docker web service. In Render:

1. Create a Supabase project and copy its PostgreSQL connection string into `ConnectionStrings__Postgres`.
2. Create an Upstash Redis database and copy its TLS connection string into `Redis__Configuration`.
3. Create a long random value for `ShortLink__AdminApiKey`.
4. Set `ShortLink__BaseUrl` to the Render service URL, such as `https://shortlink-api.onrender.com`.
5. Create the service from the repository's `render.yaml` and keep the secret values private.

The blueprint enables `Database__ApplyMigrations=true` and disables public metrics for the single free instance. Render's proxy mode enables one trusted forwarded hop so rate limiting sees the client IP. Do not expose the container directly outside the hosting provider when using `ForwardedHeaders__TrustAll=true`.

Possible alternatives are Railway, Fly.io, Azure Container Apps, or Google Cloud Run, but their free allowances and database offerings differ. A deployment always needs an API host, PostgreSQL, Redis, HTTPS, and secret storage in addition to GitHub Pages.
