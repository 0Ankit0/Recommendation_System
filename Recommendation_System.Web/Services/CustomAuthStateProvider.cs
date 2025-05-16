using Microsoft.AspNetCore.Authentication.BearerToken;
using Microsoft.AspNetCore.Components.Authorization;
using Microsoft.AspNetCore.Http;
using System.Security.Claims;
using System.Threading.Tasks;

public class CustomAuthStateProvider : AuthenticationStateProvider
{
    private readonly TokenService _tokenService;
    private readonly IHttpContextAccessor _httpContextAccessor;

    public CustomAuthStateProvider(TokenService tokenService, IHttpContextAccessor httpContextAccessor)
    {
        _tokenService = tokenService;
        _httpContextAccessor = httpContextAccessor;
    }

    public override async Task<AuthenticationState> GetAuthenticationStateAsync()
    {
        var httpContext = _httpContextAccessor.HttpContext;
        ClaimsPrincipal user = new ClaimsPrincipal(new ClaimsIdentity());

        if (httpContext != null && httpContext.Request.Cookies.TryGetValue("DeviceId", out var deviceId))
        {
            var redisData = await _tokenService.GetTokenAsync(deviceId);
            if (!string.IsNullOrEmpty(redisData))
            {
                var tokenData = System.Text.Json.JsonSerializer.Deserialize<AccessTokenResponse>(redisData);
                var identity = new ClaimsIdentity(new[] { new Claim(ClaimTypes.Name, tokenData?.AccessToken ?? "") }, "apiauth_type");
                user = new ClaimsPrincipal(identity);
            }
        }

        return new AuthenticationState(user);
    }

    public async Task MarkUserAsAuthenticated(string userName)
    {
        var authenticatedUser = new ClaimsPrincipal(new ClaimsIdentity(new[] { new Claim(ClaimTypes.Name, userName) }, "apiauth_type"));
        NotifyAuthenticationStateChanged(Task.FromResult(new AuthenticationState(authenticatedUser)));
    }
    public async Task MarkUserAsLoggedOut()
    {
        var anonymousUser = new ClaimsPrincipal(new ClaimsIdentity());
        NotifyAuthenticationStateChanged(Task.FromResult(new AuthenticationState(anonymousUser)));
    }
    public void NotifyUserAuthenticationChanged()
    {
        NotifyAuthenticationStateChanged(GetAuthenticationStateAsync());
    }
}