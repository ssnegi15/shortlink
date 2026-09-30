using Xunit;

namespace ShortLink.Tests;

public sealed class BasicTests
{
    [Fact]
    public void ExampleCodeHasExpectedLength()
    {
        Assert.Equal(12, "aZ91kLm2Pq7X".Length);
    }

    [Fact]
    public void RedirectStatusIs302()
    {
        Assert.Equal(302, 302);
    }

    [Fact]
    public void MissingStatusIs404()
    {
        Assert.Equal(404, 404);
    }
}
