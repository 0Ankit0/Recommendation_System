using System.Net.Http;
using System.Net.Http.Headers;
using System.Security.Claims;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;

namespace Recommendation_System.Web;

public class AuthorizationMessageHandler : DelegatingHandler
{
    private readonly TokenService _tokenService;
    private readonly IHttpContextAccessor _httpContextAccessor;

    public AuthorizationMessageHandler(TokenService tokenService, IHttpContextAccessor httpContextAccessor)
    {
        _tokenService = tokenService;
        _httpContextAccessor = httpContextAccessor;
    }

    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        // Retrieve the user ID from the claims in the current HTTP context
        var userId = _httpContextAccessor.HttpContext?.User?.FindFirst(ClaimTypes.NameIdentifier)?.Value;

        if (!string.IsNullOrEmpty(userId))
        {
            var token = await _tokenService.GetTokenAsync(userId);
            if (!string.IsNullOrEmpty(token))
            {
                request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
            }
        }

        return await base.SendAsync(request, cancellationToken);
    }
}
