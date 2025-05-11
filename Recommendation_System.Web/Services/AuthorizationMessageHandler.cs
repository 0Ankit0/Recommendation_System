using System.Net.Http;
using System.Net.Http.Headers;
using System.Security.Claims;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Authentication.BearerToken;
using Microsoft.AspNetCore.Http;

namespace Recommendation_System.Web;

public class AuthorizationMessageHandler(TokenService _tokenService, IHttpContextAccessor httpContextAccessor) : DelegatingHandler
{
    private readonly IHttpContextAccessor _httpContextAccessor = httpContextAccessor;
        
    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        var httpContext = _httpContextAccessor.HttpContext;
        if (httpContext != null && httpContext.Request.Cookies.TryGetValue("DeviceId", out var deviceId))
        {
            var redisData = _tokenService.GetTokenAsync(deviceId).Result;
            if (string.IsNullOrEmpty(redisData))
            {
                // Handle the case where the token is not found
                httpContext.Response.StatusCode = StatusCodes.Status401Unauthorized;
                await httpContext.Response.WriteAsync("Unauthorized");
                return new HttpResponseMessage(System.Net.HttpStatusCode.Unauthorized);
            }
            var tokenData = JsonSerializer.Deserialize<AccessTokenResponse>(redisData);
            if (!string.IsNullOrEmpty(tokenData?.AccessToken))
            {
                request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", tokenData.AccessToken);
            }
        }
        return await base.SendAsync(request, cancellationToken);
    }
}
