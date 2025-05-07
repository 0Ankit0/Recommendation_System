using StackExchange.Redis;

public class TokenService
{
    private readonly IConnectionMultiplexer _redis;

    public TokenService(IConnectionMultiplexer redis)
    {
        _redis = redis;
    }

    public async Task SetTokenAsync(string key, string token, TimeSpan expiration)
    {
        var db = _redis.GetDatabase();
        await db.StringSetAsync(key, token, expiration);
    }

    public async Task<string?> GetTokenAsync(string key)
    {
        var db = _redis.GetDatabase();
        return await db.StringGetAsync(key);
    }

    public async Task RemoveTokenAsync(string key)
    {
        var db = _redis.GetDatabase();
        await db.KeyDeleteAsync(key);
    }
}
