using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using System.Threading.Tasks;

namespace Recommendation_System.Web
{
    // You may need to install the Microsoft.AspNetCore.Http.Abstractions package into your project
    public class DeviceIdHandlerMiddleware
    {
        private readonly RequestDelegate _next;

        public DeviceIdHandlerMiddleware(RequestDelegate next)
        {
            _next = next;
        }

        public Task InvokeAsync(HttpContext httpContext)
        {
            const string DeviceIdCookieName = "DeviceId";

            // Check if the DeviceId cookie exists
            if (!httpContext.Request.Cookies.TryGetValue(DeviceIdCookieName, out var deviceId))
            {
                // Generate and set the DeviceId cookie
                deviceId = Guid.NewGuid().ToString();
                httpContext.Response.Cookies.Append(DeviceIdCookieName, deviceId, new CookieOptions
                {
                    HttpOnly = true,
                    Secure = true,
                    SameSite = SameSiteMode.Strict,
                    Expires = DateTimeOffset.UtcNow.AddYears(1)
                });
            }

            // Add the DeviceId to the request headers
            httpContext.Request.Headers["X-Device-Id"] = deviceId;


            return _next(httpContext);
        }
    }

    // Extension method used to add the middleware to the HTTP request pipeline.
    public static class DeviceIdHandlerMiddlewareExtensions
    {
        public static IApplicationBuilder UseDeviceIdHandlerMiddleware(this IApplicationBuilder builder)
        {
            return builder.UseMiddleware<DeviceIdHandlerMiddleware>();
        }
    }
}
