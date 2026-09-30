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
