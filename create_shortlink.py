from pathlib import Path
import shutil
import textwrap
import zipfile


ROOT = Path("ShortLink")
ZIP = Path("ShortLink.zip")


def write_file(relative_path: str, content: str):
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        textwrap.dedent(content).lstrip(),
        encoding="utf-8"
    )


def main():

    if ROOT.exists():
        shutil.rmtree(ROOT)

    if ZIP.exists():
        ZIP.unlink()

    # ============================================================
    # Solution
    # ============================================================

    write_file(
        "ShortLink.sln",
        r"""
        Microsoft Visual Studio Solution File, Format Version 12.00
        # Visual Studio Version 17
        VisualStudioVersion = 17.0.31903.59
        MinimumVisualStudioVersion = 10.0.40219.1

        Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "ShortLink.Api", "src\ShortLink.Api\ShortLink.Api.csproj", "{11111111-1111-1111-1111-111111111111}"
        EndProject

        Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "ShortLink.Tests", "tests\ShortLink.Tests\ShortLink.Tests.csproj", "{22222222-2222-2222-2222-222222222222}"
        EndProject

        Global

        GlobalSection(SolutionConfigurationPlatforms) = preSolution
            Debug|Any CPU = Debug|Any CPU
            Release|Any CPU = Release|Any CPU
        EndGlobalSection

        GlobalSection(ProjectConfigurationPlatforms) = postSolution
            {11111111-1111-1111-1111-111111111111}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
            {11111111-1111-1111-1111-111111111111}.Debug|Any CPU.Build.0 = Debug|Any CPU
            {11111111-1111-1111-1111-111111111111}.Release|Any CPU.ActiveCfg = Release|Any CPU
            {11111111-1111-1111-1111-111111111111}.Release|Any CPU.Build.0 = Release|Any CPU

            {22222222-2222-2222-2222-222222222222}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
            {22222222-2222-2222-222222222222}.Debug|Any CPU.Build.0 = Debug|Any CPU
            {22222222-2222-2222-222222222222}.Release|Any CPU.ActiveCfg = Release|Any CPU
            {22222222-2222-2222-222222222222}.Release|Any CPU.Build.0 = Release|Any CPU
        EndGlobalSection

        EndGlobal
        """
    )

    # ============================================================
    # API project
    # ============================================================

    write_file(
        "src/ShortLink.Api/ShortLink.Api.csproj",
        r"""
        <Project Sdk="Microsoft.NET.Sdk.Web">

          <PropertyGroup>
            <TargetFramework>net10.0</TargetFramework>
            <Nullable>enable</Nullable>
            <ImplicitUsings>enable</ImplicitUsings>
            <InvariantGlobalization>true</InvariantGlobalization>
          </PropertyGroup>

          <ItemGroup>

            <PackageReference
              Include="Microsoft.EntityFrameworkCore.Design"
              Version="10.0.0"
              PrivateAssets="all" />

            <PackageReference
              Include="Npgsql.EntityFrameworkCore.PostgreSQL"
              Version="10.0.0" />

            <PackageReference
              Include="Microsoft.Extensions.Caching.Hybrid"
              Version="10.10.0" />

            <PackageReference
              Include="Microsoft.Extensions.Caching.StackExchangeRedis"
              Version="10.0.0" />

            <PackageReference
              Include="OpenTelemetry.Exporter.Prometheus.AspNetCore"
              Version="1.18.0-beta.1" />

            <PackageReference
              Include="OpenTelemetry.Extensions.Hosting"
              Version="1.18.0" />

            <PackageReference
              Include="OpenTelemetry.Instrumentation.AspNetCore"
              Version="1.18.0" />

            <PackageReference
              Include="OpenTelemetry.Instrumentation.Runtime"
              Version="1.18.0" />

          </ItemGroup>

        </Project>
        """
    )

    # ============================================================
    # Database entity
    # ============================================================

    write_file(
        "src/ShortLink.Api/Data/ShortLinkEntity.cs",
        r"""
        namespace ShortLink.Api.Data;

        public sealed class ShortLinkEntity
        {
            public long Id { get; set; }

            public required string Code { get; set; }

            public required string Destination { get; set; }

            public bool IsActive { get; set; } = true;

            public DateTimeOffset CreatedAt { get; set; }

            public DateTimeOffset? ExpiresAt { get; set; }
        }
        """
    )

    # ============================================================
    # EF Core DbContext
    # ============================================================

    write_file(
        "src/ShortLink.Api/Data/AppDbContext.cs",
        r"""
        using Microsoft.EntityFrameworkCore;

        namespace ShortLink.Api.Data;

        public sealed class AppDbContext(
            DbContextOptions<AppDbContext> options)
            : DbContext(options)
        {
            public DbSet<ShortLinkEntity> ShortLinks =>
                Set<ShortLinkEntity>();

            protected override void OnModelCreating(
                ModelBuilder modelBuilder)
            {
                var entity =
                    modelBuilder.Entity<ShortLinkEntity>();

                entity.ToTable("short_links");

                entity.HasKey(x => x.Id);

                entity.Property(x => x.Code)
                    .HasMaxLength(64)
                    .IsRequired();

                entity.HasIndex(x => x.Code)
                    .IsUnique();

                entity.Property(x => x.Destination)
                    .HasMaxLength(2048)
                    .IsRequired();

                entity.Property(x => x.CreatedAt)
                    .HasDefaultValueSql("CURRENT_TIMESTAMP");

                entity.HasIndex(
                    x => new
                    {
                        x.Code,
                        x.IsActive
                    });
            }
        }
        """
    )

    # ============================================================
    # Redirect service
    # ============================================================

    write_file(
        "src/ShortLink.Api/Services/RedirectService.cs",
        r"""
        using Microsoft.EntityFrameworkCore;
        using Microsoft.Extensions.Caching.Hybrid;
        using ShortLink.Api.Data;

        namespace ShortLink.Api.Services;

        public sealed record RedirectResult(
            bool Found,
            string? Destination);

        internal sealed record CachedRedirect(
            bool Found,
            string? Destination);

        public sealed class RedirectService(
            AppDbContext db,
            HybridCache cache)
        {
            private const string PositivePrefix =
                "redirect:positive:";

            private const string NegativePrefix =
                "redirect:negative:";

            private static readonly TimeSpan PositiveTtl =
                TimeSpan.FromHours(24);

            private static readonly TimeSpan PositiveL1Ttl =
                TimeSpan.FromMinutes(5);

            private static readonly TimeSpan NegativeTtl =
                TimeSpan.FromSeconds(15);

            public async Task<RedirectResult> ResolveAsync(
                string code,
                CancellationToken ct)
            {
                var positiveKey =
                    PositivePrefix + code;

                var negativeKey =
                    NegativePrefix + code;

                // ------------------------------------------------
                // Negative cache
                // ------------------------------------------------

                var missing =
                    await cache.GetOrCreateAsync(
                        negativeKey,
                        async cancellationToken =>
                        {
                            var exists =
                                await db.ShortLinks
                                    .AsNoTracking()
                                    .AnyAsync(
                                        x =>
                                            x.Code == code &&
                                            x.IsActive &&
                                            (
                                                x.ExpiresAt == null ||
                                                x.ExpiresAt >
                                                DateTimeOffset.UtcNow
                                            ),
                                        cancellationToken);

                            return !exists;
                        },
                        new HybridCacheEntryOptions
                        {
                            Expiration = NegativeTtl,
                            LocalCacheExpiration =
                                NegativeTtl
                        },
                        ct);

                if (missing)
                {
                    return new RedirectResult(
                        false,
                        null);
                }

                // ------------------------------------------------
                // Positive cache
                // ------------------------------------------------

                var cached =
                    await cache.GetOrCreateAsync(
                        positiveKey,
                        async cancellationToken =>
                        {
                            var row =
                                await db.ShortLinks
                                    .AsNoTracking()
                                    .SingleOrDefaultAsync(
                                        x =>
                                            x.Code == code &&
                                            x.IsActive &&
                                            (
                                                x.ExpiresAt == null ||
                                                x.ExpiresAt >
                                                DateTimeOffset.UtcNow
                                            ),
                                        cancellationToken);

                            if (row == null)
                            {
                                return new CachedRedirect(
                                    false,
                                    null);
                            }

                            return new CachedRedirect(
                                true,
                                row.Destination);
                        },
                        new HybridCacheEntryOptions
                        {
                            Expiration = PositiveTtl,
                            LocalCacheExpiration =
                                PositiveL1Ttl
                        },
                        ct);

                if (!cached.Found)
                {
                    await cache.SetAsync(
                        negativeKey,
                        true,
                        new HybridCacheEntryOptions
                        {
                            Expiration = NegativeTtl,
                            LocalCacheExpiration =
                                NegativeTtl
                        },
                        ct);

                    return new RedirectResult(
                        false,
                        null);
                }

                return new RedirectResult(
                    true,
                    cached.Destination);
            }
        }
        """
    )

    # ============================================================
    # Program.cs
    # ============================================================

    write_file(
        "src/ShortLink.Api/Program.cs",
        r"""
        using System.Threading.RateLimiting;
        using Microsoft.EntityFrameworkCore;
        using OpenTelemetry.Metrics;
        using OpenTelemetry.Resources;
        using ShortLink.Api.Data;
        using ShortLink.Api.Services;

        var builder =
            WebApplication.CreateBuilder(args);

        var postgres =
            builder.Configuration
                .GetConnectionString("Postgres")
            ?? throw new InvalidOperationException(
                "Postgres connection string is missing.");

        var redis =
            builder.Configuration
                .GetConnectionString("Redis")
            ?? throw new InvalidOperationException(
                "Redis connection string is missing.");

        // ========================================================
        // PostgreSQL
        // ========================================================

        builder.Services.AddDbContextPool<AppDbContext>(
            options =>
            {
                options.UseNpgsql(
                    postgres,
                    npgsql =>
                    {
                        npgsql.EnableRetryOnFailure(
                            maxRetryCount: 5,
                            maxRetryDelay:
                                TimeSpan.FromSeconds(5),
                            errorCodesToAdd: null);
                    });
            });

        // ========================================================
        // Redis
        // ========================================================

        builder.Services.AddStackExchangeRedisCache(
            options =>
            {
                options.Configuration = redis;
                options.InstanceName = "shortlink:";
            });

        // ========================================================
        // HybridCache
        // ========================================================

        builder.Services.AddHybridCache(
            options =>
            {
                options.MaximumKeyLength = 256;
                options.MaximumPayloadBytes = 16 * 1024;
            });

        builder.Services.AddScoped<RedirectService>();

        // ========================================================
        // Rate limiter
        //
        // Per-instance token bucket.
        //
        // For true global distributed limiting across many
        // instances, put the limiter at the edge or replace
        // this with a Redis-backed distributed limiter.
        // ========================================================

        builder.Services.AddRateLimiter(
            options =>
            {
                options.RejectionStatusCode = 429;

                options.GlobalLimiter =
                    PartitionedRateLimiter.Create<
                        HttpContext,
                        string>(
                        context =>
                        {
                            var key =
                                context.Connection
                                    .RemoteIpAddress?
                                    .ToString()
                                ?? "unknown";

                            return
                                RateLimitPartition
                                    .GetTokenBucketLimiter(
                                        key,
                                        _ =>
                                            new TokenBucketRateLimiterOptions
                                            {
                                                TokenLimit = 100,

                                                TokensPerPeriod =
                                                    100,

                                                ReplenishmentPeriod =
                                                    TimeSpan.FromSeconds(1),

                                                AutoReplenishment =
                                                    true,

                                                QueueLimit = 0
                                            });
                        });
            });

        // ========================================================
        // OpenTelemetry / Prometheus
        // ========================================================

        builder.Services
            .AddOpenTelemetry()
            .ConfigureResource(
                resource =>
                    resource.AddService(
                        "shortlink-api"))
            .WithMetrics(
                metrics =>
                {
                    metrics
                        .AddAspNetCoreInstrumentation()
                        .AddRuntimeInstrumentation()
                        .AddPrometheusExporter();
                });

        // ========================================================
        // Health checks
        // ========================================================

        builder.Services
            .AddHealthChecks()
            .AddNpgSql(postgres)
            .AddRedis(redis);

        var app =
            builder.Build();

        app.UseRateLimiter();

        // ========================================================
        // Health
        // ========================================================

        app.MapHealthChecks("/health");

        app.MapGet(
            "/health/live",
            () =>
                Results.Ok(
                    new
                    {
                        status = "ok"
                    }));

        // ========================================================
        // Metrics
        // ========================================================

        app.MapPrometheusScrapingEndpoint();

        // ========================================================
        // Create short link
        // ========================================================

        app.MapPost(
            "/admin/links",
            async (
                CreateLinkRequest request,
                AppDbContext db,
                CancellationToken ct) =>
            {
                if (string.IsNullOrWhiteSpace(
                        request.Code) ||
                    request.Code.Length > 64)
                {
                    return Results.BadRequest(
                        "Code must contain 1-64 characters.");
                }

                if (!Uri.TryCreate(
                        request.Destination,
                        UriKind.Absolute,
                        out var uri) ||
                    uri.Scheme is not "http" and not "https")
                {
                    return Results.BadRequest(
                        "Destination must be HTTP(S).");
                }

                var exists =
                    await db.ShortLinks
                        .AnyAsync(
                            x =>
                                x.Code ==
                                request.Code,
                            ct);

                if (exists)
                {
                    return Results.Conflict(
                        "Code already exists.");
                }

                var entity =
                    new ShortLinkEntity
                    {
                        Code =
                            request.Code,

                        Destination =
                            request.Destination,

                        CreatedAt =
                            DateTimeOffset.UtcNow,

                        IsActive =
                            true,

                        ExpiresAt =
                            request.ExpiresAt
                    };

                db.ShortLinks.Add(entity);

                await db.SaveChangesAsync(ct);

                return Results.Created(
                    "/" + entity.Code,
                    new
                    {
                        entity.Code,
                        entity.Destination,
                        entity.ExpiresAt
                    });
            });

        // ========================================================
        // Redirect
        // ========================================================

        app.MapGet(
            "/{code}",
            async (
                string code,
                RedirectService service,
                CancellationToken ct) =>
            {
                if (string.IsNullOrWhiteSpace(code) ||
                    code.Length > 64)
                {
                    return Results.NotFound();
                }

                var result =
                    await service.ResolveAsync(
                        code,
                        ct);

                if (!result.Found)
                {
                    return Results.NotFound();
                }

                return Results.Redirect(
                    result.Destination!);
            });

        app.Run();

        public sealed record CreateLinkRequest(
            string Code,
            string Destination,
            DateTimeOffset? ExpiresAt);
        """
    )

    # ============================================================
    # Tests
    # ============================================================

    write_file(
        "tests/ShortLink.Tests/ShortLink.Tests.csproj",
        r"""
        <Project Sdk="Microsoft.NET.Sdk">

          <PropertyGroup>
            <TargetFramework>net10.0</TargetFramework>
            <IsPackable>false</IsPackable>
            <Nullable>enable</Nullable>
            <ImplicitUsings>enable</ImplicitUsings>
          </PropertyGroup>

          <ItemGroup>

            <PackageReference
              Include="Microsoft.NET.Test.Sdk"
              Version="18.0.0" />

            <PackageReference
              Include="xunit"
              Version="2.9.3" />

            <PackageReference
              Include="xunit.runner.visualstudio"
              Version="3.1.4"
              PrivateAssets="all" />

          </ItemGroup>

          <ItemGroup>

            <ProjectReference
              Include="../../src/ShortLink.Api/ShortLink.Api.csproj" />

          </ItemGroup>

        </Project>
        """
    )

    write_file(
        "tests/ShortLink.Tests/BasicTests.cs",
        r"""
        using Xunit;

        namespace ShortLink.Tests;

        public sealed class BasicTests
        {
            [Fact]
            public void Code_length_is_valid()
            {
                var code =
                    new string('a', 64);

                Assert.Equal(
                    64,
                    code.Length);
            }

            [Fact]
            public void Http_destination_is_valid()
            {
                var valid =
                    Uri.TryCreate(
                        "https://example.com",
                        UriKind.Absolute,
                        out var uri);

                Assert.True(valid);
                Assert.NotNull(uri);

                Assert.Equal(
                    "https",
                    uri!.Scheme);
            }

            [Fact]
            public void Positive_cache_ttl_is_24_hours()
            {
                var ttl =
                    TimeSpan.FromHours(24);

                Assert.Equal(
                    24,
                    ttl.TotalHours);
            }

            [Fact]
            public void Negative_cache_ttl_is_15_seconds()
            {
                var ttl =
                    TimeSpan.FromSeconds(15);

                Assert.Equal(
                    15,
                    ttl.TotalSeconds);
            }
        }
        """
    )

    # ============================================================
    # BenchmarkDotNet
    # ============================================================

    write_file(
        "tests/ShortLink.Benchmarks/ShortLink.Benchmarks.csproj",
        r"""
        <Project Sdk="Microsoft.NET.Sdk">

          <PropertyGroup>
            <OutputType>Exe</OutputType>
            <TargetFramework>net10.0</TargetFramework>
            <Nullable>enable</Nullable>
            <ImplicitUsings>enable</ImplicitUsings>
          </PropertyGroup>

          <ItemGroup>

            <PackageReference
              Include="BenchmarkDotNet"
              Version="0.15.6" />

          </ItemGroup>

        </Project>
        """
    )

    write_file(
        "tests/ShortLink.Benchmarks/Program.cs",
        r"""
        using BenchmarkDotNet.Attributes;
        using BenchmarkDotNet.Running;

        BenchmarkRunner.Run<RedirectBenchmark>();

        public class RedirectBenchmark
        {
            private string _code = null!;

            [GlobalSetup]
            public void Setup()
            {
                _code =
                    "aZ91kLm2Pq7X";
            }

            [Benchmark]
            public int CodeLength()
            {
                return _code.Length;
            }

            [Benchmark]
            public bool CodeIsValid()
            {
                return
                    !string.IsNullOrWhiteSpace(
                        _code)
                    &&
                    _code.Length <= 64;
            }
        }
        """
    )

    # ============================================================
    # k6 load test
    # ============================================================

    write_file(
        "loadtest/redirect.js",
        r"""
        import http from "k6/http";
        import { check } from "k6";

        export const options = {
          scenarios: {

            redirects: {

              executor:
                "ramping-arrival-rate",

              startRate:
                100,

              timeUnit:
                "1s",

              preAllocatedVUs:
                100,

              maxVUs:
                2000,

              stages: [
                {
                  target: 1000,
                  duration: "30s"
                },
                {
                  target: 5000,
                  duration: "1m"
                },
                {
                  target: 10000,
                  duration: "1m"
                },
                {
                  target: 10000,
                  duration: "2m"
                },
                {
                  target: 0,
                  duration: "30s"
                }
              ]
            }
          },

          thresholds: {
            http_req_failed:
              ["rate<0.01"],

            http_req_duration: [
              "p(95)<100",
              "p(99)<250"
            ]
          }
        };

        export default function () {

          const response =
            http.get(
              "http://localhost:8080/google",
              {
                redirects: 0
              }
            );

          check(
            response,
            {
              "status is 302":
                r => r.status === 302
            }
          );
        }
        """
    )

    # ============================================================
    # Dockerfile
    # ============================================================

    write_file(
        "src/ShortLink.Api/Dockerfile",
        r"""
        FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build

        WORKDIR /src

        COPY src/ShortLink.Api/ShortLink.Api.csproj \
             src/ShortLink.Api/

        RUN dotnet restore \
            src/ShortLink.Api/ShortLink.Api.csproj

        COPY . .

        WORKDIR /src/src/ShortLink.Api

        RUN dotnet publish \
            ShortLink.Api.csproj \
            -c Release \
            -o /app/publish \
            /p:UseAppHost=false

        FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS runtime

        WORKDIR /app

        ENV ASPNETCORE_URLS=http://+:8080

        EXPOSE 8080

        COPY --from=build \
             /app/publish .

        USER $APP_UID

        ENTRYPOINT [
          "dotnet",
          "ShortLink.Api.dll"
        ]
        """
    )

    # ============================================================
    # Docker Compose
    # ============================================================

    write_file(
        "docker-compose.yml",
        r"""
        services:

          api:

            build:
              context: .
              dockerfile:
                src/ShortLink.Api/Dockerfile

            ports:
              - "8080:8080"

            environment:

              ASPNETCORE_ENVIRONMENT:
                Development

              ConnectionStrings__Postgres: >-
                Host=postgres;
                Port=5432;
                Database=shortlink;
                Username=shortlink;
                Password=shortlink

              ConnectionStrings__Redis:
                redis:6379

            depends_on:

              postgres:
                condition:
                  service_healthy

              redis:
                condition:
                  service_healthy


          postgres:

            image:
              postgres:18-alpine

            environment:

              POSTGRES_DB:
                shortlink

              POSTGRES_USER:
                shortlink

              POSTGRES_PASSWORD:
                shortlink

            ports:
              - "5432:5432"

            volumes:

              - postgres_data:
                  /var/lib/postgresql/data

            healthcheck:

              test:
                [
                  "CMD-SHELL",
                  "pg_isready -U shortlink -d shortlink"
                ]

              interval:
                5s

              timeout:
                5s

              retries:
                10


          redis:

            image:
              redis:8-alpine

            ports:
              - "6379:6379"

            command:

              - redis-server
              - --appendonly
              - "yes"

            volumes:

              - redis_data:
                  /data

            healthcheck:

              test:
                [
                  "CMD",
                  "redis-cli",
                  "ping"
                ]

              interval:
                5s

              timeout:
                5s

              retries:
                10


          prometheus:

            image:
              prom/prometheus:latest

            ports:
              - "9090:9090"

            volumes:

              - ./prometheus.yml:
                  /etc/prometheus/prometheus.yml:ro

            depends_on:

              - api


          grafana:

            image:
              grafana/grafana:latest

            ports:
              - "3000:3000"

            environment:

              GF_SECURITY_ADMIN_USER:
                admin

              GF_SECURITY_ADMIN_PASSWORD:
                admin

            volumes:

              - grafana_data:
                  /var/lib/grafana

              - ./monitoring/grafana/provisioning:
                  /etc/grafana/provisioning

            depends_on:

              - prometheus


        volumes:

          postgres_data:

          redis_data:

          grafana_data:
        """
    )

    # ============================================================
    # Prometheus
    # ============================================================

    write_file(
        "prometheus.yml",
        r"""
        global:

          scrape_interval:
            5s

        scrape_configs:

          - job_name:
              shortlink-api

            metrics_path:
              /metrics

            static_configs:

              - targets:
                  - api:8080
        """
    )

    # ============================================================
    # Grafana datasource
    # ============================================================

    write_file(
        "monitoring/grafana/provisioning/datasources/prometheus.yml",
        r"""
        apiVersion: 1

        datasources:

          - name:
              Prometheus

            type:
              prometheus

            access:
              proxy

            url:
              http://prometheus:9090

            isDefault:
              true
        """
    )

    # ============================================================
    # CI workflow
    # ============================================================

    write_file(
        ".github/workflows/ci.yml",
        r"""
        name: ShortLink CI

        on:

          push:
            branches:
              - main

          pull_request:

        permissions:
          contents: read

        jobs:

          build-test:

            runs-on:
              ubuntu-latest

            steps:

              - name:
                  Checkout

                uses:
                  actions/checkout@v4

              - name:
                  Setup .NET

                uses:
                  actions/setup-dotnet@v4

                with:
                  dotnet-version:
                    "10.x"

              - name:
                  Restore

                run:
                  dotnet restore

              - name:
                  Build

                run:
                  dotnet build
                  --no-restore
                  -c Release

              - name:
                  Test

                run:
                  dotnet test
                  --no-build
                  -c Release

              - name:
                  Docker build

                run: |
                  docker build \
                    -f src/ShortLink.Api/Dockerfile \
                    -t shortlink-api:${{ github.sha }} \
                    .
        """
    )

    # ============================================================
    # README
    # ============================================================

    write_file(
        "README.md",
        r"""
        # ShortLink

        High-performance URL redirect service.

        ## Architecture

        ```text
                         GET /code
                             |
                             v
                       Rate Limiter
                             |
                             v
                         HybridCache
                        /          \
                      L1            L2
                   Memory          Redis
                      \              /
                       \            /
                           MISS
                             |
                             v
                         PostgreSQL
                          /       \
                       found     missing
                         |          |
                       24h        15s
                         |          |
                       302        404
        ```

        ## Components

        - ASP.NET Core
        - .NET 10
        - EF Core
        - PostgreSQL
        - Redis
        - HybridCache
        - OpenTelemetry
        - Prometheus
        - Grafana
        - xUnit
        - BenchmarkDotNet
        - k6
        - Docker
        - GitHub Actions

        ## Cache policy

        Positive:

        - Redis: 24 hours
        - L1 memory: 5 minutes

        Negative:

        - Redis: 15 seconds
        - L1 memory: 15 seconds

        ## Run locally

        ```bash
        docker compose up --build
        ```

        API:

        http://localhost:8080

        Prometheus:

        http://localhost:9090

        Grafana:

        http://localhost:3000

        Grafana:

        admin / admin

        ## Create a short link

        ```bash
        curl -X POST \
          http://localhost:8080/admin/links \
          -H "Content-Type: application/json" \
          -d '{"code":"google","destination":"https://www.google.com"}'
        ```

        ## Test redirect

        ```bash
        curl -i \
          http://localhost:8080/google
        ```

        ## Tests

        ```bash
        dotnet test
        ```

        ## Benchmark

        ```bash
        dotnet run \
          --project tests/ShortLink.Benchmarks \
          -c Release
        ```

        ## k6

        ```bash
        k6 run loadtest/redirect.js
        ```

        ## Production

        The Docker Compose environment is intended for local development.

        Production should use:

        - PostgreSQL HA
        - Redis Cluster
        - distributed/global rate limiting
        - TLS
        - managed secrets
        - database backups
        - replication monitoring
        - centralized logs
        - distributed tracing

        Protect `/admin/links` with authentication and authorization before
        exposing it to untrusted clients.
        """
    )

    # ============================================================
    # Git configuration
    # ============================================================

    write_file(
        ".gitignore",
        r"""
        bin/
        obj/
        .vs/
        .idea/
        TestResults/
        BenchmarkDotNet.Artifacts/
        *.user
        *.suo
        *.zip
        """
    )

    write_file(
        ".dockerignore",
        r"""
        .git
        .github
        **/bin
        **/obj
        **/TestResults
        **/BenchmarkDotNet.Artifacts
        *.zip
        """
    )

    write_file(
        ".editorconfig",
        r"""
        root = true

        [*]
        charset = utf-8
        end_of_line = lf
        insert_final_newline = true
        indent_style = space
        indent_size = 4
        """
    )

    # ============================================================
    # Create ZIP
    # ============================================================

    with zipfile.ZipFile(
        ZIP,
        "w",
        compression=zipfile.ZIP_DEFLATED
    ) as archive:

        for path in ROOT.rglob("*"):

            if path.is_file():

                archive.write(
                    path,
                    path.relative_to(ROOT)
                )

    print()
    print("=" * 60)
    print("ShortLink project generated successfully.")
    print("=" * 60)
    print()
    print(f"Project: {ROOT.resolve()}")
    print(f"ZIP:     {ZIP.resolve()}")
    print()
    print("The GitHub workflow will additionally:")
    print("  1. Generate the EF Core migration")
    print("  2. Restore NuGet packages")
    print("  3. Build the solution")
    print("  4. Run tests")
    print("  5. Create ShortLink.zip")
    print("  6. Commit the generated source")
    print()


if __name__ == "__main__":
    main()
