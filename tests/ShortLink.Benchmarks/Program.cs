using BenchmarkDotNet.Attributes;
using BenchmarkDotNet.Running;

BenchmarkRunner.Run<ShortLinkBenchmarks>();

[MemoryDiagnoser]
public class ShortLinkBenchmarks
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
}
