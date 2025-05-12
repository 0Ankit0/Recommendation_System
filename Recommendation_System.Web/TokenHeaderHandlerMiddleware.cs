using Microsoft.AspNetCore.Authentication.BearerToken;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Threading.Tasks;

namespace Recommendation_System.Web
{
    // You may need to install the Microsoft.AspNetCore.Http.Abstractions package into your project
    public class TokenHeaderHandlerMiddleware(RequestDelegate _next, TokenService _tokenService)
    {


        public Task Invoke(HttpContext httpContext)
        {
            var deviceId = httpContext.Request.Headers["X-Device-Id"];
            var redisData = _tokenService.GetTokenAsync(deviceId).Result;
            if (!string.IsNullOrEmpty(redisData))
            {
                AccessTokenResponse? tokenData = JsonSerializer.Deserialize<AccessTokenResponse>(redisData);
                httpContext.Request.Headers["Authorization"] = $"Bearer {tokenData?.AccessToken}";
            }
            return _next(httpContext);
        }
    }

    // Extension method used to add the middleware to the HTTP request pipeline.
    public static class TokenHeaderHandlerMiddlewareExtensions
    {
        public static IApplicationBuilder UseTokenHeaderHandlerMiddleware(this IApplicationBuilder builder)
        {
            return builder.UseMiddleware<TokenHeaderHandlerMiddleware>();
        }
    }
}
