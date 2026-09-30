using ShortLink.Api.Services;
using Xunit;

namespace ShortLink.Tests;

public sealed class BasicTests
{
    [Fact]
    public void NonExpiringLinkIsNotExpired()
    {
        var result = new RedirectResult(true, "https://example.com");

        Assert.False(result.IsExpired(DateTimeOffset.UtcNow));
    }

    [Fact]
    public void ExpiredLinkIsExpired()
    {
        var now = new DateTimeOffset(2026, 9, 30, 12, 0, 0, TimeSpan.Zero);
        var result = new RedirectResult(true, "https://example.com", now.AddSeconds(-1));

        Assert.True(result.IsExpired(now));
    }

    [Fact]
    public void FutureLinkIsNotExpired()
    {
        var now = new DateTimeOffset(2026, 9, 30, 12, 0, 0, TimeSpan.Zero);
        var result = new RedirectResult(true, "https://example.com", now.AddSeconds(1));

        Assert.False(result.IsExpired(now));
    }
}
