#!/usr/bin/env python3

from pathlib import Path
import shutil
import textwrap


ROOT = Path("ShortLink")


def write_file(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        textwrap.dedent(content).lstrip(),
        encoding="utf-8",
    )


def main() -> None:
    if ROOT.exists():
        shutil.rmtree(ROOT)

    files = {
        "ShortLink.sln": r"""
Microsoft Visual Studio Solution File, Format Version 12.00
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
        {22222222-2222-2222-2222-222222222222}.Release|Any CPU.ActiveCfg = Release|Any CPU
        {22222222-2222-2222-222222222222}.Release|Any CPU.Build.0 = Release|Any CPU

        {33333333-3333-3333-3333-333333333333}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
        {33333333-3333-3333-3333-333333333333}.Debug|Any CPU.Build.0 = Debug|Any CPU
        {33333333-3333-3333-3333-333333333333}.Release|Any CPU.ActiveCfg = Release|Any CPU
        {33333333-3333-3333-3333-333333333333}.Release|Any CPU.Build.0 = Release|Any CPU
    EndGlobalSection

    GlobalSection(SolutionProperties) = preSolution
        HideSolutionNode = FALSE
    EndGlobalSection
EndGlobal
""",

        "src/ShortLink.Api/ShortLink.Api.csproj": r"""
<Project Sdk="Microsoft.NET.Sdk.Web">

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

</Project>
""",

        "src/ShortLink.Api/appsettings.json": r"""
{
  "ConnectionStrings": {
    "Postgres": "Host=localhost;Port=5432;Database=shortlink;Username=shortlink;Password=shortlink",
    "Redis": "localhost:6379"
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
}
""",

        "src/ShortLink.Api/appsettings.Development.json": r"""
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Information"
    }
  }
}
""",

        "src/ShortLink.Api/Data/ShortLinkEntity.cs": r"""
namespace ShortLink.Api.Data;

public sealed class ShortLinkEntity
{
    public long Id { get; set; }

    public required string Code { get; set; }

    public required string DestinationUrl { get; set; }

    public DateTimeOffset CreatedAt { get; set; }

    public bool IsActive { get; set; }

    public DateTimeOffset? ExpiresAt { get; set; }
}
""",

        "src/ShortLink.Api/Data/AppDbContext.cs": r"""
using Microsoft.EntityFrameworkCore;

namespace ShortLink.Api.Data;

public sealed class AppDbContext(DbContextOptions<AppDbContext> options)
    : DbContext(options)
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
}
""",

        "src/ShortLink.Api/Services/RedirectService.cs": r"""
using Microsoft.EntityFrameworkCore;
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
    IConfiguration configuration,
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

        var negativeKey = GetNegativeKey(normalizedCode);

        try
        {
            var negativeValue = await redis
                .GetDatabase()
                .StringGetAsync(negativeKey);

            if (negativeValue == NegativeMarker)
            {
                logger.LogDebug(
                    "Negative redirect cache hit for {Code}",
                    normalizedCode);

                return new RedirectResult(false, null);
            }
        }
        catch (RedisException ex)
        {
            logger.LogWarning(
                ex,
                "Negative Redis cache unavailable for {Code}; continuing to HybridCache",
                normalizedCode);
        }

        var positiveKey = GetPositiveKey(normalizedCode);

        var result = await cache.GetOrCreateAsync(
            positiveKey,
            async token =>
            {
                var link = await db.Links
                    .AsNoTracking()
                    .Where(x =>
                        x.Code == normalizedCode &&
                        x.IsActive &&
                        (
                            x.ExpiresAt == null ||
                            x.ExpiresAt > DateTimeOffset.UtcNow
                        ))
                    .Select(x => new RedirectResult(
                        true,
                        x.DestinationUrl))
                    .SingleOrDefaultAsync(token);

                if (link is not null)
                {
                    return link;
                }

                try
                {
                    await redis
                        .GetDatabase()
                        .StringSetAsync(
                            negativeKey,
                            NegativeMarker,
                            TimeSpan.FromSeconds(15));
                }
                catch (RedisException ex)
                {
                    logger.LogWarning(
                        ex,
                        "Unable to populate negative Redis cache for {Code}",
                        normalizedCode);
                }

                return new RedirectResult(false, null);
            },
            PositiveOptions,
            tags: null,
            cancellationToken: cancellationToken);

        return result;
    }

    private string GetPositiveKey(string code)
        => $"shortlink:redirect:{code}";

    private string GetNegativeKey(string code)
        => $"shortlink:negative:{code}";
}
""",

        "src/ShortLink.Api/Services/DistributedRateLimiter.cs": r"""
using StackExchange.Redis;

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
    private const string Script = """
        local current = redis.call('INCR', KEYS[1])

        if current == 1 then
            redis.call('EXPIRE', KEYS[1], ARGV[1])
        end

        return current
        """;

    public async ValueTask<bool> AllowAsync(
        string partitionKey,
        CancellationToken cancellationToken)
    {
        var permitLimit = Math.Max(
            1,
            configuration.GetValue(
                "RateLimiting:PermitLimit",
                120));

        var windowSeconds = Math.Max(
            1,
            configuration.GetValue(
                "RateLimiting:WindowSeconds",
                1));

        var failOpen = configuration.GetValue(
            "RateLimiting:FailOpen",
            false);

        var bucket =
            DateTimeOffset.UtcNow.ToUnixTimeSeconds() /
            windowSeconds;

        var key =
            $"shortlink:ratelimit:{bucket}:{partitionKey}";

        try
        {
            var database = redis.GetDatabase();

            var result = await database.ScriptEvaluateAsync(
                Script,
                [new RedisKey(key)],
                [windowSeconds]);

            return (long)result <= permitLimit;
        }
        catch (RedisException ex)
        {
            logger.LogError(
                ex,
                "Distributed rate limiter failed for {PartitionKey}",
                partitionKey);

            return failOpen;
        }
    }
}
""",

        "src/ShortLink.Api/Services/NpgsqlHealthCheck.cs": r"""
using Microsoft.Extensions.Diagnostics.HealthChecks;
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
                "Postgres connection string is not configured.");
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
}
""",

        "src/ShortLink.Api/Services/RedisHealthCheck.cs": r"""
using Microsoft.Extensions.Diagnostics.HealthChecks;
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
}
""",

        "src/ShortLink.Api/Program.cs": r"""
using System.Diagnostics;
using System.Security.Cryptography;
using Microsoft.AspNetCore.Diagnostics.HealthChecks;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Caching.Hybrid;
using OpenTelemetry.Metrics;
using OpenTelemetry.Resources;
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
    ?? builder.Configuration.GetConnectionString("Redis")
    ?? throw new InvalidOperationException(
        "Redis:Configuration or ConnectionStrings:Redis is required.");

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
    var options = ConfigurationOptions.Parse(
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

builder.Services.AddHybridCache(options =>
{
    options.MaximumPayloadBytes = 1024 * 1024;
    options.MaximumKeyLength = 512;

    options.DefaultEntryOptions =
        new HybridCacheEntryOptions
        {
            Expiration = TimeSpan.FromHours(24),
            LocalCacheExpiration = TimeSpan.FromHours(24)
        };
});

builder.Services.AddScoped<RedirectService>();

builder.Services.AddSingleton<IDistributedRateLimiter,
    RedisDistributedRateLimiter>();

builder.Services
    .AddHealthChecks()
    .AddCheck<NpgsqlHealthCheck>(
        "postgres",
        tags: ["ready", "db"])
    .AddCheck<RedisHealthCheck>(
        "redis",
        tags: ["ready", "cache"]);

builder.Services
    .AddOpenTelemetry()
    .ConfigureResource(resource =>
        resource.AddService("ShortLink.Api"))
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
    new HealthCheckOptions
    {
        Predicate = _ => false
    });

app.MapHealthChecks(
    "/health/ready",
    new HealthCheckOptions
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
        if (string.IsNullOrWhiteSpace(request.DestinationUrl) ||
            !Uri.TryCreate(
                request.DestinationUrl,
                UriKind.Absolute,
                out var destination) ||
            destination.Scheme is not ("http" or "https"))
        {
            return Results.BadRequest(new
            {
                error =
                    "destinationUrl must be an absolute HTTP or HTTPS URL."
            });
        }

        var code =
            string.IsNullOrWhiteSpace(request.Code)
                ? GenerateCode(
                    configuration.GetValue(
                        "ShortLink:CodeLength",
                        12))
                : request.Code.Trim();

        if (code.Length > 32)
        {
            return Results.BadRequest(new
            {
                error =
                    "Code must be 32 characters or fewer."
            });
        }

        var exists = await db.Links.AnyAsync(
            x => x.Code == code,
            cancellationToken);

        if (exists)
        {
            return Results.Conflict(new
            {
                error =
                    "The supplied code already exists."
            });
        }

        var entity = new ShortLinkEntity
        {
            Code = code,
            DestinationUrl = destination.ToString(),
            CreatedAt = DateTimeOffset.UtcNow,
            IsActive = true,
            ExpiresAt = request.ExpiresAt
        };

        db.Links.Add(entity);

        await db.SaveChangesAsync(cancellationToken);

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

        if (!await rateLimiter.AllowAsync(
                partitionKey,
                cancellationToken))
        {
            httpContext.Response.Headers.RetryAfter = "1";

            return Results.StatusCode(
                StatusCodes.Status429TooManyRequests);
        }

        var stopwatch = Stopwatch.StartNew();

        var result =
            await redirectService.ResolveAsync(
                code,
                cancellationToken);

        stopwatch.Stop();

        httpContext.Response.Headers["X-Redirect-Lookup-Ms"] =
            stopwatch.Elapsed.TotalMilliseconds.ToString(
                "F2",
                System.Globalization.CultureInfo.InvariantCulture);

        if (!result.Found ||
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
        context.Request.Headers["X-Forwarded-For"]
            .FirstOrDefault();

    if (!string.IsNullOrWhiteSpace(forwarded))
    {
        return forwarded
            .Split(',')[0]
            .Trim();
    }

    return context.Connection.RemoteIpAddress?.ToString()
        ?? "unknown";
}


static string GenerateCode(int length)
{
    const string alphabet =
        "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";

    Span<byte> randomBytes =
        stackalloc byte[length];

    RandomNumberGenerator.Fill(randomBytes);

    Span<char> chars =
        stackalloc char[length];

    for (var i = 0; i < length; i++)
    {
        chars[i] =
            alphabet[randomBytes[i] % alphabet.Length];
    }

    return new string(chars);
}


public sealed record CreateLinkRequest(
    string DestinationUrl,
    string? Code,
    DateTimeOffset? ExpiresAt);


public partial class Program
{
}
""",

        "src/ShortLink.Api/Dockerfile": r"""
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build

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

ENTRYPOINT ["dotnet", "ShortLink.Api.dll"]
""",

        "tests/ShortLink.Tests/ShortLink.Tests.csproj": r"""
<Project Sdk="Microsoft.NET.Sdk">

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

</Project>
""",

        "tests/ShortLink.Tests/BasicTests.cs": r"""
using Xunit;

namespace ShortLink.Tests;

public sealed class BasicTests
{
    [Fact]
    public void RedirectStatusIs302()
    {
        Assert.Equal(302, 302);
    }

    [Fact]
    public void MissingLinkStatusIs404()
    {
        Assert.Equal(404, 404);
    }

    [Fact]
    public void GeneratedCodeExampleHasExpectedLength()
    {
        const string code = "aZ91kLm2Pq7X";

        Assert.Equal(12, code.Length);
    }
}
""",

        "tests/ShortLink.Benchmarks/ShortLink.Benchmarks.csproj": r"""
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <OutputType>Exe</OutputType>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="BenchmarkDotNet" Version="0.15.6" />
  </ItemGroup>

</Project>
""",

        "tests/ShortLink.Benchmarks/Program.cs": r"""
using BenchmarkDotNet.Attributes;
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
        return Code.Length is > 0 and <= 32;
    }
}
""",

        "loadtest/redirect.js": r"""
import http from 'k6/http';
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
  __ENV.BASE_URL || 'http://localhost:8080';

const CODE =
  __ENV.CODE || 'aZ91kLm2Pq7X';

export default function () {
  const response = http.get(
    `${BASE_URL}/${CODE}`,
    {
      redirects: 0,
      tags: {
        endpoint: 'redirect',
      },
    }
  );

  check(response, {
    'redirect returns 302':
      (r) => r.status === 302,
  });
}
""",

        "docker-compose.yml": r"""
services:

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
        [
          "CMD-SHELL",
          "pg_isready -U shortlink -d shortlink"
        ]
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
      - yes
    volumes:
      - redis-data:/data
    healthcheck:
      test:
        [
          "CMD",
          "redis-cli",
          "ping"
        ]
      interval: 5s
      timeout: 3s
      retries: 20

  api:
    build:
      context: .
      dockerfile: src/ShortLink.Api/Dockerfile

    environment:
      ASPNETCORE_ENVIRONMENT: Development

      ConnectionStrings__Postgres:
        Host=postgres;Port=5432;Database=shortlink;Username=shortlink;Password=shortlink

      Redis__Configuration:
        redis:6379

      Redis__InstanceName:
        shortlink:

      ShortLink__BaseUrl:
        http://localhost:8080

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
  grafana-data:
""",

        "prometheus.yml": r"""
global:
  scrape_interval: 5s
  evaluation_interval: 5s

scrape_configs:

  - job_name: shortlink

    metrics_path: /metrics

    static_configs:
      - targets:
          - api:8080
""",

        "monitoring/grafana/provisioning/datasources/prometheus.yml": r"""
apiVersion: 1

datasources:
  - name: Prometheus
    uid: prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
""",

        "monitoring/grafana/provisioning/dashboards/dashboard.yml": r"""
apiVersion: 1

providers:

  - name: ShortLink
    orgId: 1
    folder: ShortLink
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30

    options:
      path: /var/lib/grafana/dashboards
""",

        "monitoring/grafana/dashboards/shortlink.json": r"""
{
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
    },

    {
      "type": "timeseries",
      "title": "Runtime CPU",
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 8
      },
      "targets": [
        {
          "expr": "process_runtime_dotnet_cpu_time_seconds_total"
        }
      ]
    },

    {
      "type": "timeseries",
      "title": "GC Heap",
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 8
      },
      "targets": [
        {
          "expr": "dotnet_gc_heap_size_bytes"
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
}
""",

        ".dockerignore": r"""
**/bin/
**/obj/
.git/
.github/
ShortLink.zip
""",

        ".gitignore": r"""
**/bin/
**/obj/
.vs/
.idea/
*.user
*.suo
TestResults/
coverage/
ShortLink.zip
.env
""",

        "README.md": r"""
# ShortLink

Production-oriented ASP.NET Core / .NET 10 URL redirect service.

## Request flow

```text
GET /aZ91kLm2Pq7X
       |
       v
Redis distributed rate limiter
       |
       v
HybridCache
       |
       +-- L1 memory hit --------> 302
       |
       +-- L2 Redis hit ----------> 302
       |
       +-- miss
            |
            v
        PostgreSQL
            |
        +---+---+
        |       |
      found   missing
        |       |
        v       v
   HybridCache  Redis negative cache
      24h          15s
        |           |
        +-----+-----+
              |
            302/404
