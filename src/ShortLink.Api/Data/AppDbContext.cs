using Microsoft.EntityFrameworkCore;

namespace ShortLink.Api.Data;

public sealed class AppDbContext(
    DbContextOptions<AppDbContext> options)
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

        link.HasIndex(x => x.Code).IsUnique();

        link.Property(x => x.DestinationUrl)
            .HasMaxLength(2048)
            .IsRequired();

        link.Property(x => x.CreatedAt).IsRequired();
        link.Property(x => x.IsActive).IsRequired();

        link.HasIndex(x => new { x.Code, x.IsActive });
    }
}
