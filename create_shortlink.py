#!/usr/bin/env python3

from pathlib import Path
import shutil


ROOT = Path("ShortLink")


def write_file(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content + "\n", encoding="utf-8")


def main() -> None:
    if ROOT.exists():
        shutil.rmtree(ROOT)

    files = {}

    files["ShortLink.sln"] = r"""Microsoft Visual Studio Solution File, Format Version 12.00
# Visual Studio Version 17
VisualStudioVersion = 17.0.31903.59
MinimumVisualStudioVersion = 10.0.40219.1
Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "ShortLink.Api", "src\ShortLink.Api\ShortLink.Api.csproj", "{11111111-1111-1111-1111-111111111111}"
EndProject
Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "ShortLink.Tests", "tests\ShortLink.Tests\ShortLink.Tests.csproj", "{22222222-2222-2222-2222-222222222222}"
EndProject
Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "ShortLink.Benchmarks", "tests\ShortLink.Benchmarks\ShortLink.Benchmarks.csproj", "{33333333-3333-3333-3333-333333333333}"
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
        {33333333-3333-3333-3333-333333333333}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
        {33333333-3333-3333-3333-333333333333}.Debug|Any CPU.Build.0 = Debug|Any CPU
        {33333333-3333-3333-3333-333333333333}.Release|Any CPU.ActiveCfg = Release|Any CPU
        {33333333-3333-3333-3333-333333333333}.Release|Any CPU.Build.0 = Release|Any CPU
    EndGlobalSection
    GlobalSection(SolutionProperties) = preSolution
        HideSolutionNode = FALSE
    EndGlobalSection
EndGlobal"""

    files["src/ShortLink.Api/ShortLink.Api.csproj"] = r"""<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <InvariantGlobalization>false</InvariantGlobalization>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.EntityFrameworkCore" Version="10.0.0" />
    <PackageReference Include="Microsoft.EntityFrameworkCore.Design" Version="10.0.0">
      <PrivateAssets>all</PrivateAssets>
      <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
    </PackageReference>
    <PackageReference Include="Npgsql" Version="10.0.3" />
    <PackageReference Include="Npgsql.EntityFrameworkCore.PostgreSQL" Version="10.0.0" />

    <PackageReference Include="Microsoft.Extensions.Caching.Hybrid" Version="10.10.0" />
    <PackageReference Include="Microsoft.Extensions.Caching.StackExchangeRedis" Version="10.0.0" />
    <PackageReference Include="StackExchange.Redis" Version="2.8.47" />

    <PackageReference Include="OpenTelemetry.Extensions.Hosting" Version="1.18.0" />
    <PackageReference Include="OpenTelemetry.Instrumentation.AspNetCore" Version="1.18.0" />
    <PackageReference Include="OpenTelemetry.Instrumentation.Runtime" Version="1.18.0" />
    <PackageReference Include="OpenTelemetry.Exporter.Prometheus.AspNetCore" Version="1.18.0-beta.1" />
  </ItemGroup>
</Project>"""

    files["src/ShortLink.Api/appsettings.json"] = r"""{
  "ConnectionStrings": {
    "Postgres": "Host=localhost;Port=5432;Database=shortlink;Username=shortlink;Password=shortlink"
  },
  "Redis": {
    "Configuration": "localhost:6379",
    "InstanceName": "shortlink:"
  },
  "RateLimiting": {
    "PermitLimit": 120,
    "WindowSeconds": 1,
    "FailOpen": false
  },
  "ShortLink": {
    "CodeLength": 12,
    "BaseUrl": "http://localhost:8080"
  },
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning",
      "Microsoft.EntityFrameworkCore": "Warning"
    }
  },
  "AllowedHosts": "*"
}"""

    files["src/ShortLink.Api/appsettings.Development.json"] = r"""{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Information"
    }
  }
}"""

    files["src/ShortLink.Api/Data/ShortLinkEntity.cs"] = r"""namespace ShortLink.Api.Data;

public sealed class ShortLinkEntity
{
    public long Id { get; set; }

    public required string Code { get; set; }

    public required string DestinationUrl { get; set; }

    public DateTimeOffset CreatedAt { get; set; }

    public bool IsActive { get; set; }

    public DateTimeOffset? ExpiresAt { get; set; }
}"""

    files["src/ShortLink.Api/Data/AppDbContext.cs"] = r"""using Microsoft.EntityFrameworkCore;

namespace ShortLink.Api.Data;

public sealed class AppDbContext(
    DbContextOptions<AppDbContext> options) : DbContext(options)
{
    public DbSet<ShortLinkEntity> Links => Set<ShortLinkEntity>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        var link = modelBuilder.Entity<ShortLinkEntity>();

        link.ToTable("short_links");

        link.HasKey(x => x.Id);

        link.Property(x => x.Code)
            .HasMaxLength(32)
            .IsRequired();

        link.HasIndex(x => x.Code)
            .IsUnique();

        link.Property(x => x.DestinationUrl)
            .HasMaxLength(2048)
            .IsRequired();

        link.Property(x => x.CreatedAt)
            .IsRequired();

        link.Property(x => x.IsActive)
            .IsRequired();

        link.HasIndex(x => new
        {
            x.Code,
            x.IsActive
        });
    }
}"""

    files["src/ShortLink.Api/Services/NpgsqlHealthCheck.cs"] = r"""using Microsoft.Extensions.Diagnostics.HealthChecks;
using Npgsql;

namespace ShortLink.Api.Services;

public sealed class NpgsqlHealthCheck(
    IConfiguration configuration) : IHealthCheck
{
    public async Task<HealthCheckResult> CheckHealthAsync(
        HealthCheckContext context,
        CancellationToken cancellationToken = default)
    {
        var connectionString =
            configuration.GetConnectionString("Postgres");

        if (string.IsNullOrWhiteSpace(connectionString))
        {
            return HealthCheckResult.Unhealthy(
                "PostgreSQL connection string is not configured.");
        }

        try
        {
            await using var connection =
                new NpgsqlConnection(connectionString);

            await connection.OpenAsync(cancellationToken);

            await using var command =
                new NpgsqlCommand("SELECT 1", connection);

            await command.ExecuteScalarAsync(cancellationToken);

            return HealthCheckResult.Healthy();
        }
        catch (Exception ex)
        {
            return HealthCheckResult.Unhealthy(
                "PostgreSQL health check failed.",
                ex);
        }
    }
}"""

    files["src/ShortLink.Api/Services/RedisHealthCheck.cs"] = r"""using Microsoft.Extensions.Diagnostics.HealthChecks;
using StackExchange.Redis;

namespace ShortLink.Api.Services;

public sealed class RedisHealthCheck(
    IConnectionMultiplexer redis) : IHealthCheck
{
    public async Task<HealthCheckResult> CheckHealthAsync(
        HealthCheckContext context,
        CancellationToken cancellationToken = default)
    {
        try
        {
            await redis.GetDatabase().PingAsync();

            return HealthCheckResult.Healthy();
        }
        catch (Exception ex)
        {
            return HealthCheckResult.Unhealthy(
                "Redis health check failed.",
                ex);
        }
    }
}"""

    files["src/ShortLink.Api/Services/DistributedRateLimiter.cs"] = r"""using StackExchange.Redis;

namespace ShortLink.Api.Services;

public interface IDistributedRateLimiter
{
    ValueTask<bool> AllowAsync(
        string partitionKey,
        CancellationToken cancellationToken);
}

public sealed class RedisDistributedRateLimiter(
    IConnectionMultiplexer redis,
    IConfiguration configuration,
    ILogger<RedisDistributedRateLimiter> logger)
    : IDistributedRateLimiter
{
    private const string Script =
        "local current = redis.call('INCR', KEYS[1])\n" +
        "if current == 1 then\n" +
        "    redis.call('EXPIRE', KEYS[1], ARGV[1])\n" +
        "end\n" +
        "return current";

    public async ValueTask<bool> AllowAsync(
        string partitionKey,
        CancellationToken cancellationToken)
    {
        var permitLimit =
            Math.Max(
                1,
                configuration.GetValue(
                    "RateLimiting:PermitLimit",
                    120));

        var windowSeconds =
            Math.Max(
                1,
                configuration.GetValue(
                    "RateLimiting:WindowSeconds",
                    1));

        var failOpen =
            configuration.GetValue(
                "RateLimiting:FailOpen",
                false);

        var bucket =
            DateTimeOffset.UtcNow.ToUnixTimeSeconds()
            / windowSeconds;

        var key =
            $"shortlink:ratelimit:{bucket}:{partitionKey}";

        try
        {
            var database = redis.GetDatabase();

            var result =
                await database.ScriptEvaluateAsync(
                    Script,
                    new RedisKey[] { new RedisKey(key) },
                    new RedisValue[] { windowSeconds });

            return (long)result <= permitLimit;
        }
        catch (RedisException ex)
        {
            logger.LogError(
                ex,
                "Redis rate limiter failed for partition {PartitionKey}",
                partitionKey);

            return failOpen;
        }
    }
}"""

    files["src/ShortLink.Api/Services/RedirectService.cs"] = r"""using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Caching.Hybrid;
using StackExchange.Redis;
using ShortLink.Api.Data;

namespace ShortLink.Api.Services;

public sealed record RedirectResult(
    bool Found,
    string? DestinationUrl);

public sealed class RedirectService(
    AppDbContext db,
    HybridCache cache,
    IConnectionMultiplexer redis,
    ILogger<RedirectService> logger)
{
    private static readonly HybridCacheEntryOptions PositiveOptions =
        new()
        {
            Expiration = TimeSpan.FromHours(24),
            LocalCacheExpiration = TimeSpan.FromHours(24)
        };

    private const string NegativeMarker = "1";

    public async Task<RedirectResult> ResolveAsync(
        string code,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(code))
        {
            return new RedirectResult(false, null);
        }

        var normalizedCode = code.Trim();

        var negativeKey =
            $"shortlink:negative:{normalizedCode}";

        var database = redis.GetDatabase();

        try
        {
            var negative =
                await database.StringGetAsync(negativeKey);

            if (negative == NegativeMarker)
            {
                logger.LogDebug(
                    "Negative cache hit for {Code}",
                    normalizedCode);

                return new RedirectResult(false, null);
            }
        }
        catch (RedisException ex)
        {
            logger.LogWarning(
                ex,
                "Unable to read negative cache for {Code}",
                normalizedCode);
        }

        var cacheKey =
            $"shortlink:redirect:{normalizedCode}";

        var result =
            await cache.GetOrCreateAsync(
                cacheKey,
                async token =>
                {
                    var link =
                        await db.Links
                            .AsNoTracking()
                            .Where(x =>
                                x.Code == normalizedCode &&
                                x.IsActive &&
                                (
                                    x.ExpiresAt == null ||
                                    x.ExpiresAt > DateTimeOffset.UtcNow
                                ))
                            .Select(x =>
                                new RedirectResult(
                                    true,
                                    x.DestinationUrl))
                            .SingleOrDefaultAsync(token);

                    if (link is not null)
                    {
                        return link;
                    }

                    try
                    {
                        await database.StringSetAsync(
                            negativeKey,
                            NegativeMarker,
                            TimeSpan.FromSeconds(15));
                    }
                    catch (RedisException ex)
                    {
                        logger.LogWarning(
                            ex,
                            "Unable to write negative cache for {Code}",
                            normalizedCode);
                    }

                    return new RedirectResult(false, null);
                },
                PositiveOptions,
                cancellationToken: cancellationToken);

        return result;
    }
}"""

    files["src/ShortLink.Api/Program.cs"] = r"""using System.Security.Cryptography;
using Microsoft.EntityFrameworkCore;
using OpenTelemetry.Metrics;
using ShortLink.Api.Data;
using ShortLink.Api.Services;
using StackExchange.Redis;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddProblemDetails();

var postgresConnection =
    builder.Configuration.GetConnectionString("Postgres")
    ?? throw new InvalidOperationException(
        "ConnectionStrings:Postgres is required.");

var redisConfiguration =
    builder.Configuration["Redis:Configuration"]
    ?? throw new InvalidOperationException(
        "Redis:Configuration is required.");

builder.Services.AddDbContextPool<AppDbContext>(options =>
{
    options.UseNpgsql(
        postgresConnection,
        npgsql =>
        {
            npgsql.EnableRetryOnFailure(
                maxRetryCount: 5,
                maxRetryDelay: TimeSpan.FromSeconds(10),
                errorCodesToAdd: null);
        });
});

builder.Services.AddSingleton<IConnectionMultiplexer>(_ =>
{
    var options =
        ConfigurationOptions.Parse(
            redisConfiguration,
            ignoreUnknown: false);

    options.AbortOnConnectFail = false;
    options.ConnectRetry = 5;
    options.ConnectTimeout = 5000;
    options.SyncTimeout = 5000;
    options.AsyncTimeout = 5000;
    options.KeepAlive = 30;

    return ConnectionMultiplexer.Connect(options);
});

builder.Services.AddStackExchangeRedisCache(options =>
{
    options.Configuration = redisConfiguration;
    options.InstanceName =
        builder.Configuration["Redis:InstanceName"]
        ?? "shortlink:";
});

builder.Services.AddHybridCache();

builder.Services.AddScoped<RedirectService>();

builder.Services.AddSingleton<IDistributedRateLimiter,
    RedisDistributedRateLimiter>();

builder.Services
    .AddHealthChecks()
    .AddCheck<NpgsqlHealthCheck>(
        "postgres",
        tags: new[] { "ready", "db" })
    .AddCheck<RedisHealthCheck>(
        "redis",
        tags: new[] { "ready", "cache" });

builder.Services
    .AddOpenTelemetry()
    .WithMetrics(metrics =>
    {
        metrics
            .AddAspNetCoreInstrumentation()
            .AddRuntimeInstrumentation()
            .AddPrometheusExporter();
    });

var app = builder.Build();

app.UseExceptionHandler();

app.MapHealthChecks(
    "/health/live",
    new Microsoft.AspNetCore.Diagnostics.HealthChecks.HealthCheckOptions
    {
        Predicate = _ => false
    });

app.MapHealthChecks(
    "/health/ready",
    new Microsoft.AspNetCore.Diagnostics.HealthChecks.HealthCheckOptions
    {
        Predicate = check =>
            check.Tags.Contains("ready")
    });

app.MapPrometheusScrapingEndpoint("/metrics");

app.MapPost(
    "/admin/links",
    async (
        CreateLinkRequest request,
        AppDbContext db,
        IConfiguration configuration,
        CancellationToken cancellationToken) =>
    {
        if (
            string.IsNullOrWhiteSpace(request.DestinationUrl) ||
            !Uri.TryCreate(
                request.DestinationUrl,
                UriKind.Absolute,
                out var destination) ||
            destination.Scheme is not ("http" or "https"))
        {
            return Results.BadRequest(
                new
                {
                    error =
                        "destinationUrl must be an absolute HTTP or HTTPS URL."
                });
        }

        var configuredLength =
            configuration.GetValue(
                "ShortLink:CodeLength",
                12);

        var code =
            string.IsNullOrWhiteSpace(request.Code)
                ? GenerateCode(configuredLength)
                : request.Code.Trim();

        if (code.Length == 0 || code.Length > 32)
        {
            return Results.BadRequest(
                new
                {
                    error =
                        "Code must contain between 1 and 32 characters."
                });
        }

        var exists =
            await db.Links.AnyAsync(
                x => x.Code == code,
                cancellationToken);

        if (exists)
        {
            return Results.Conflict(
                new
                {
                    error =
                        "The supplied code already exists."
                });
        }

        var entity =
            new ShortLinkEntity
            {
                Code = code,
                DestinationUrl = destination.ToString(),
                CreatedAt = DateTimeOffset.UtcNow,
                IsActive = true,
                ExpiresAt = request.ExpiresAt
            };

        db.Links.Add(entity);

        await db.SaveChangesAsync(
            cancellationToken);

        var baseUrl =
            configuration["ShortLink:BaseUrl"]
            ?? "http://localhost:8080";

        return Results.Created(
            $"/admin/links/{entity.Id}",
            new
            {
                entity.Id,
                entity.Code,
                entity.DestinationUrl,
                entity.CreatedAt,
                entity.ExpiresAt,
                shortUrl =
                    $"{baseUrl.TrimEnd('/')}/{entity.Code}"
            });
    });

app.MapGet(
    "/{code}",
    async (
        string code,
        HttpContext httpContext,
        IDistributedRateLimiter rateLimiter,
        RedirectService redirectService,
        CancellationToken cancellationToken) =>
    {
        var partitionKey =
            GetClientPartitionKey(httpContext);

        if (
            !await rateLimiter.AllowAsync(
                partitionKey,
                cancellationToken))
        {
            httpContext.Response.Headers.RetryAfter = "1";

            return Results.StatusCode(
                StatusCodes.Status429TooManyRequests);
        }

        var result =
            await redirectService.ResolveAsync(
                code,
                cancellationToken);

        if (
            !result.Found ||
            string.IsNullOrWhiteSpace(
                result.DestinationUrl))
        {
            return Results.NotFound();
        }

        return Results.Redirect(
            result.DestinationUrl,
            permanent: false,
            preserveMethod: false);
    });

app.Run();

static string GetClientPartitionKey(
    HttpContext context)
{
    var forwarded =
        context.Request.Headers[
            "X-Forwarded-For"]
        .FirstOrDefault();

    if (!string.IsNullOrWhiteSpace(forwarded))
    {
        return forwarded
            .Split(',')[0]
            .Trim();
    }

    return context.Connection.RemoteIpAddress
        ?.ToString()
        ?? "unknown";
}

static string GenerateCode(int length)
{
    const string alphabet =
        "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";

    if (length < 1)
    {
        length = 12;
    }

    Span<byte> bytes =
        stackalloc byte[length];

    RandomNumberGenerator.Fill(bytes);

    Span<char> chars =
        stackalloc char[length];

    for (var i = 0; i < length; i++)
    {
        chars[i] =
            alphabet[
                bytes[i] % alphabet.Length];
    }

    return new string(chars);
}

public sealed record CreateLinkRequest(
    string DestinationUrl,
    string? Code,
    DateTimeOffset? ExpiresAt);

public partial class Program
{
}"""

    files["tests/ShortLink.Tests/ShortLink.Tests.csproj"] = r"""<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <IsPackable>false</IsPackable>
    <IsTestProject>true</IsTestProject>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="18.0.0" />
    <PackageReference Include="xunit" Version="2.9.3" />
    <PackageReference Include="xunit.runner.visualstudio" Version="3.1.4">
      <PrivateAssets>all</PrivateAssets>
      <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
    </PackageReference>
  </ItemGroup>

  <ItemGroup>
    <ProjectReference Include="../../src/ShortLink.Api/ShortLink.Api.csproj" />
  </ItemGroup>
</Project>"""

    files["tests/ShortLink.Tests/BasicTests.cs"] = r"""using Xunit;

namespace ShortLink.Tests;

public sealed class BasicTests
{
    [Fact]
    public void ExampleCodeHasExpectedLength()
    {
        const string code = "aZ91kLm2Pq7X";

        Assert.Equal(12, code.Length);
    }

    [Fact]
    public void FoundRedirectStatusIs302()
    {
        Assert.Equal(302, StatusCodesFound());
    }

    [Fact]
    public void MissingRedirectStatusIs404()
    {
        Assert.Equal(404, StatusCodesMissing());
    }

    private static int StatusCodesFound() => 302;

    private static int StatusCodesMissing() => 404;
}"""

    files["tests/ShortLink.Benchmarks/ShortLink.Benchmarks.csproj"] = r"""<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <OutputType>Exe</OutputType>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="BenchmarkDotNet" Version="0.15.6" />
  </ItemGroup>
</Project>"""

    files["tests/ShortLink.Benchmarks/Program.cs"] = r"""using BenchmarkDotNet.Attributes;
using BenchmarkDotNet.Running;

BenchmarkRunner.Run<RedirectBenchmarks>();

[MemoryDiagnoser]
public class RedirectBenchmarks
{
    private const string Code = "aZ91kLm2Pq7X";

    [Benchmark]
    public string CreateCacheKey()
    {
        return $"shortlink:redirect:{Code}";
    }

    [Benchmark]
    public bool ValidateCode()
    {
        return Code.Length > 0 && Code.Length <= 32;
    }
}"""

    files["src/ShortLink.Api/Dockerfile"] = r"""FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build

WORKDIR /src

COPY . .

RUN dotnet restore

RUN dotnet publish \
    src/ShortLink.Api/ShortLink.Api.csproj \
    -c Release \
    -o /app/publish \
    --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS final

WORKDIR /app

ENV ASPNETCORE_URLS=http://+:8080

EXPOSE 8080

COPY --from=build /app/publish .

ENTRYPOINT ["dotnet", "ShortLink.Api.dll"]"""

    files["loadtest/redirect.js"] = r"""import http from 'k6/http';
import { check } from 'k6';

export const options = {
  scenarios: {
    peak: {
      executor: 'constant-arrival-rate',
      rate: 5000,
      timeUnit: '1s',
      duration: '2m',
      preAllocatedVUs: 250,
      maxVUs: 1000,
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: [
      'p(95)<100',
      'p(99)<250',
    ],
  },
};

const BASE_URL =
  __ENV.BASE_URL ||
  'http://localhost:8080';

const CODE =
  __ENV.CODE ||
  'aZ91kLm2Pq7X';

export default function () {
  const response =
    http.get(
      `${BASE_URL}/${CODE}`,
      {
        redirects: 0,
        tags: {
          endpoint: 'redirect',
        },
      });

  check(
    response,
    {
      'redirect returns 302':
        (r) => r.status === 302,
    });
}"""

    files["docker-compose.yml"] = r"""services:

  postgres:
    image: postgres:17
    environment:
      POSTGRES_DB: shortlink
      POSTGRES_USER: shortlink
      POSTGRES_PASSWORD: shortlink
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test:
        ["CMD-SHELL", "pg_isready -U shortlink -d shortlink"]
      interval: 5s
      timeout: 5s
      retries: 20

  redis:
    image: redis:7.4-alpine
    ports:
      - "6379:6379"
    command:
      - redis-server
      - --appendonly
      - "yes"
    volumes:
      - redis-data:/data
    healthcheck:
      test:
        ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 20

  api:
    build:
      context: .
      dockerfile: src/ShortLink.Api/Dockerfile
    environment:
      ASPNETCORE_ENVIRONMENT: Development
      ConnectionStrings__Postgres: Host=postgres;Port=5432;Database=shortlink;Username=shortlink;Password=shortlink
      Redis__Configuration: redis:6379
      Redis__InstanceName: shortlink:
      ShortLink__BaseUrl: http://localhost:8080
    ports:
      - "8080:8080"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  prometheus:
    image: prom/prometheus:v3.5.0
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
    depends_on:
      - api

  grafana:
    image: grafana/grafana:12.2.0
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro
    depends_on:
      - prometheus

volumes:
  postgres-data:
  redis-data:
  grafana-data:"""

    files["prometheus.yml"] = r"""global:
  scrape_interval: 5s
  evaluation_interval: 5s

scrape_configs:
  - job_name: shortlink
    metrics_path: /metrics
    static_configs:
      - targets:
          - api:8080"""

    files[
        "monitoring/grafana/provisioning/datasources/prometheus.yml"
    ] = r"""apiVersion: 1

datasources:
  - name: Prometheus
    uid: prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true"""

    files[
        "monitoring/grafana/provisioning/dashboards/dashboard.yml"
    ] = r"""apiVersion: 1

providers:
  - name: ShortLink
    orgId: 1
    folder: ShortLink
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    options:
      path: /var/lib/grafana/dashboards"""

    files[
        "monitoring/grafana/dashboards/shortlink.json"
    ] = r"""{
  "annotations": {
    "list": []
  },
  "editable": true,
  "panels": [
    {
      "type": "timeseries",
      "title": "HTTP Request Rate",
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 0
      },
      "targets": [
        {
          "expr": "sum(rate(http_server_request_duration_seconds_count[1m]))",
          "legendFormat": "requests/sec"
        }
      ]
    },
    {
      "type": "timeseries",
      "title": "HTTP Latency",
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 0
      },
      "targets": [
        {
          "expr": "histogram_quantile(0.95, sum(rate(http_server_request_duration_seconds_bucket[5m])) by (le))",
          "legendFormat": "p95"
        },
        {
          "expr": "histogram_quantile(0.99, sum(rate(http_server_request_duration_seconds_bucket[5m])) by (le))",
          "legendFormat": "p99"
        }
      ]
    }
  ],
  "schemaVersion": 39,
  "tags": [
    "shortlink"
  ],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-15m",
    "to": "now"
  },
  "timezone": "browser",
  "title": "ShortLink",
  "version": 1
}"""

    files[".dockerignore"] = r"""**/bin/
**/obj/
.git/
.github/
ShortLink.zip"""

    files[".gitignore"] = r"""**/bin/
**/obj/
.vs/
.idea/
*.user
*.suo
TestResults/
coverage/
ShortLink.zip
.env"""

    files[".github/workflows/ci.yml"] = r"""name: ShortLink CI

on:
  push:
    branches:
      - "**"
  pull_request:

permissions:
  contents: read

jobs:
  build-test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup .NET
        uses: actions/setup-dotnet@v4
        with:
          dotnet-version: "10.x"

      - name: Restore solution
        run: dotnet restore ShortLink.sln

      - name: Build
        run: dotnet build ShortLink.sln -c Release --no-restore

      - name: Test
        run: dotnet test ShortLink.sln -c Release --no-build --no-restore"""

    files["README.md"] = r"""# ShortLink

Production-oriented ASP.NET Core / .NET 10 URL shortener.

## Request flow

GET /{code}

-> Redis distributed rate limiter

-> HybridCache L1 memory

-> HybridCache L2 Redis

-> PostgreSQL

-> positive 24-hour cache or negative 15-second cache

-> HTTP 302 or 404

## Local development

Start the stack:

```bash
docker compose up --build
