using StackExchange.Redis;

//Keep track of the token along with the device id of the user so that they can log out of any device from anywhere
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
