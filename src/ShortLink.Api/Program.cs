using System.Security.Cryptography;
using Microsoft.AspNetCore.Diagnostics.HealthChecks;
using Microsoft.AspNetCore.HttpOverrides;
using Microsoft.EntityFrameworkCore;
using Npgsql;
using OpenTelemetry.Metrics;
using ShortLink.Api.Data;
using ShortLink.Api.Services;
using StackExchange.Redis;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddProblemDetails();

builder.Services.Configure<ForwardedHeadersOptions>(options =>
{
    options.ForwardedHeaders = ForwardedHeaders.XForwardedFor |
                               ForwardedHeaders.XForwardedProto;

    var knownProxies = builder.Configuration
        .GetSection("ForwardedHeaders:KnownProxies")
        .Get<string[]>() ?? [];

    foreach (var address in knownProxies)
    {
        if (System.Net.IPAddress.TryParse(address, out var ipAddress))
            options.KnownProxies.Add(ipAddress);
    }

    if (builder.Configuration.GetValue<bool>("ForwardedHeaders:TrustAll"))
    {
        options.KnownProxies.Clear();
        options.KnownIPNetworks.Clear();
        options.KnownIPNetworks.Add(new System.Net.IPNetwork(
            System.Net.IPAddress.Any,
            0));
        options.ForwardLimit = 1;
    }
});

var postgres = builder.Configuration.GetConnectionString("Postgres")
    ?? throw new InvalidOperationException("ConnectionStrings:Postgres is required.");

var redisConfiguration = builder.Configuration["Redis:Configuration"]
    ?? throw new InvalidOperationException("Redis:Configuration is required.");

builder.Services.AddDbContextPool<AppDbContext>(options =>
{
    options.UseNpgsql(
        postgres,
        npgsql => npgsql.EnableRetryOnFailure(
            maxRetryCount: 5,
            maxRetryDelay: TimeSpan.FromSeconds(10),
            errorCodesToAdd: null));
});

builder.Services.AddSingleton<IConnectionMultiplexer>(_ =>
{
    var options = ConfigurationOptions.Parse(redisConfiguration);
    options.AbortOnConnectFail = false;
    options.ConnectRetry = 5;
    options.ConnectTimeout = 5000;
    options.AsyncTimeout = 5000;
    options.SyncTimeout = 5000;
    options.KeepAlive = 30;
    return ConnectionMultiplexer.Connect(options);
});

builder.Services.AddStackExchangeRedisCache(options =>
{
    options.Configuration = redisConfiguration;
    options.InstanceName = builder.Configuration["Redis:InstanceName"] ?? "shortlink:";
});

builder.Services.AddHybridCache();

builder.Services.AddScoped<RedirectService>();
builder.Services.AddSingleton<IDistributedRateLimiter, RedisDistributedRateLimiter>();

builder.Services.AddHealthChecks()
    .AddCheck<PostgresHealthCheck>("postgres", tags: new[] { "ready", "db" })
    .AddCheck<RedisHealthCheck>("redis", tags: new[] { "ready", "cache" });

builder.Services.AddOpenTelemetry()
    .WithMetrics(metrics =>
    {
        metrics.AddAspNetCoreInstrumentation();
        metrics.AddRuntimeInstrumentation();
        metrics.AddPrometheusExporter();
    });

var app = builder.Build();

app.UseForwardedHeaders();
app.UseExceptionHandler();

if (app.Environment.IsDevelopment() ||
    app.Configuration.GetValue<bool>("Database:ApplyMigrations"))
{
    await using var scope = app.Services.CreateAsyncScope();
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    await db.Database.MigrateAsync();
}

app.MapHealthChecks("/health/live", new HealthCheckOptions
{
    Predicate = _ => false
});

app.MapHealthChecks("/health/ready", new HealthCheckOptions
{
    Predicate = check => check.Tags.Contains("ready")
});

if (app.Configuration.GetValue<bool>("Metrics:Enabled", true))
    app.MapPrometheusScrapingEndpoint("/metrics");

app.MapPost("/admin/links", async (
    CreateLinkRequest request,
    HttpContext context,
    AppDbContext db,
    IConfiguration configuration,
    IDistributedRateLimiter rateLimiter,
    CancellationToken cancellationToken) =>
{
    var adminApiKey = configuration["ShortLink:AdminApiKey"];

    if (string.IsNullOrWhiteSpace(adminApiKey))
    {
        return Results.Problem(
            "ShortLink:AdminApiKey is not configured.",
            statusCode: StatusCodes.Status503ServiceUnavailable);
    }

    if (!HasValidAdminKey(context, adminApiKey))
        return Results.Unauthorized();

    var partitionKey = $"admin:{GetClientPartitionKey(context)}";

    if (!await rateLimiter.AllowAsync(partitionKey, cancellationToken))
    {
        context.Response.Headers.RetryAfter = "1";
        return Results.StatusCode(StatusCodes.Status429TooManyRequests);
    }

    if (string.IsNullOrWhiteSpace(request.DestinationUrl) ||
        !Uri.TryCreate(request.DestinationUrl, UriKind.Absolute, out var destination) ||
        destination.Scheme is not ("http" or "https") ||
        destination.ToString().Length > 2048)
    {
        return Results.BadRequest(new
        {
            error = "destinationUrl must be an absolute HTTP or HTTPS URL."
        });
    }

    var length = configuration.GetValue<int>("ShortLink:CodeLength", 12);

    var code = string.IsNullOrWhiteSpace(request.Code)
        ? GenerateCode(length)
        : request.Code.Trim();

    if (code.Length == 0 || code.Length > 32)
    {
        return Results.BadRequest(new
        {
            error = "Code must contain between 1 and 32 characters."
        });
    }

    if (request.ExpiresAt <= DateTimeOffset.UtcNow)
    {
        return Results.BadRequest(new
        {
            error = "expiresAt must be in the future."
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

    try
    {
        await db.SaveChangesAsync(cancellationToken);
    }
    catch (DbUpdateException ex) when
        (ex.InnerException is PostgresException
        {
            SqlState: PostgresErrorCodes.UniqueViolation
        })
    {
        return Results.Conflict(new
        {
            error = "The supplied code already exists."
        });
    }

    var baseUrl = configuration["ShortLink:BaseUrl"] ?? "http://localhost:8080";

    return Results.Created(
        $"/admin/links/{entity.Id}",
        new
        {
            entity.Id,
            entity.Code,
            entity.DestinationUrl,
            entity.CreatedAt,
            entity.ExpiresAt,
            shortUrl = $"{baseUrl.TrimEnd('/')}/{entity.Code}"
        });
});

app.MapGet("/{code}", async (
    string code,
    HttpContext context,
    IDistributedRateLimiter rateLimiter,
    RedirectService redirectService,
    CancellationToken cancellationToken) =>
{
    var partitionKey = GetClientPartitionKey(context);

    if (!await rateLimiter.AllowAsync(partitionKey, cancellationToken))
    {
        context.Response.Headers.RetryAfter = "1";
        return Results.StatusCode(StatusCodes.Status429TooManyRequests);
    }

    var result = await redirectService.ResolveAsync(code, cancellationToken);

    if (!result.Found || string.IsNullOrWhiteSpace(result.DestinationUrl))
        return Results.NotFound();

    return Results.Redirect(result.DestinationUrl, permanent: false, preserveMethod: false);
});

app.Run();

static string GetClientPartitionKey(HttpContext context)
{
    return context.Connection.RemoteIpAddress?.ToString() ?? "unknown";
}

static bool HasValidAdminKey(HttpContext context, string expectedKey)
{
    var suppliedKey = context.Request.Headers["X-Admin-Key"].FirstOrDefault();

    if (string.IsNullOrEmpty(suppliedKey))
        return false;

    var expectedBytes = System.Text.Encoding.UTF8.GetBytes(expectedKey);
    var suppliedBytes = System.Text.Encoding.UTF8.GetBytes(suppliedKey);

    return CryptographicOperations.FixedTimeEquals(expectedBytes, suppliedBytes);
}

static string GenerateCode(int length)
{
    const string alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
    length = Math.Max(1, length);

    Span<byte> bytes = stackalloc byte[length];
    RandomNumberGenerator.Fill(bytes);

    Span<char> chars = stackalloc char[length];

    for (var i = 0; i < length; i++)
        chars[i] = alphabet[bytes[i] % alphabet.Length];

    return new string(chars);
}

public sealed record CreateLinkRequest(
    string DestinationUrl,
    string? Code,
    DateTimeOffset? ExpiresAt);

public partial class Program
{
}
