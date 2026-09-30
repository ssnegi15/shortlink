using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Caching.Hybrid;
using ShortLink.Api.Data;
using StackExchange.Redis;

namespace ShortLink.Api.Services;

public sealed record RedirectResult(
    bool Found,
    string? DestinationUrl,
    DateTimeOffset? ExpiresAt = null)
{
    public bool IsExpired(DateTimeOffset now) =>
        ExpiresAt is not null && ExpiresAt <= now;
}

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

    public async Task<RedirectResult> ResolveAsync(
        string code,
        CancellationToken cancellationToken)
    {
        var normalized = code.Trim();

        if (normalized.Length == 0)
            return new RedirectResult(false, null);

        var negativeKey = $"shortlink:negative:{normalized}";
        var database = redis.GetDatabase();

        try
        {
            var negative = await database.StringGetAsync(negativeKey);

            if (negative == "1")
                return new RedirectResult(false, null);
        }
        catch (RedisException ex)
        {
            logger.LogWarning(ex,
                "Negative cache read failed for {Code}", normalized);
        }

        var cacheKey = $"shortlink:redirect:{normalized}";

        var result = await cache.GetOrCreateAsync(
            cacheKey,
            async token =>
            {
                var link = await db.Links
                    .AsNoTracking()
                    .Where(x =>
                        x.Code == normalized &&
                        x.IsActive &&
                        (x.ExpiresAt == null ||
                         x.ExpiresAt > DateTimeOffset.UtcNow))
                    .Select(x => new RedirectResult(
                        true,
                        x.DestinationUrl,
                        x.ExpiresAt))
                    .SingleOrDefaultAsync(token);

                if (link is not null)
                    return link;

                try
                {
                    await database.StringSetAsync(
                        negativeKey,
                        "1",
                        TimeSpan.FromSeconds(15));
                }
                catch (RedisException ex)
                {
                    logger.LogWarning(ex,
                        "Negative cache write failed for {Code}",
                        normalized);
                }

                return new RedirectResult(false, null);
            },
            PositiveOptions,
            cancellationToken: cancellationToken);

        if (!result.Found || result.IsExpired(DateTimeOffset.UtcNow))
        {
            await cache.RemoveAsync(cacheKey, cancellationToken);
            return new RedirectResult(false, null, result.ExpiresAt);
        }

        return result;
    }
}
