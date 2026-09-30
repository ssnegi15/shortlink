using StackExchange.Redis;

namespace ShortLink.Api.Services;

public interface IDistributedRateLimiter
{
    ValueTask<bool> AllowAsync(string partitionKey, CancellationToken cancellationToken);
}

public sealed class RedisDistributedRateLimiter(
    IConnectionMultiplexer redis,
    IConfiguration configuration,
    ILogger<RedisDistributedRateLimiter> logger)
    : IDistributedRateLimiter
{
    private const string Script =
        "local current = redis.call('INCR', KEYS[1]) "
        + "if current == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end "
        + "return current";

    public async ValueTask<bool> AllowAsync(
        string partitionKey,
        CancellationToken cancellationToken)
    {
        var limit = Math.Max(1, configuration.GetValue<int>("RateLimiting:PermitLimit", 120));
        var window = Math.Max(1, configuration.GetValue<int>("RateLimiting:WindowSeconds", 1));
        var failOpen = configuration.GetValue<bool>("RateLimiting:FailOpen", false);

        var bucket = DateTimeOffset.UtcNow.ToUnixTimeSeconds() / window;
        var key = $"shortlink:ratelimit:{bucket}:{partitionKey}";

        try
        {
            var result = await redis.GetDatabase().ScriptEvaluateAsync(
                Script,
                new RedisKey[] { key },
                new RedisValue[] { window });

            return (long)result <= limit;
        }
        catch (RedisException ex)
        {
            logger.LogError(ex,
                "Distributed rate limiter failed for {PartitionKey}",
                partitionKey);

            return failOpen;
        }
    }
}
