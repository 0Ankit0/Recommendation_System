using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;

namespace Recommendation_System.Web;

public class UserApiClient(HttpClient httpClient)
{
    public async Task<HttpResponseMessage> RegisterAsync(RegisterRequest model)
        => await httpClient.PostAsJsonAsync("/User/register", model);

    public async Task<HttpResponseMessage> LoginAsync(LoginRequest model, bool useCookies = false)
        => await httpClient.PostAsJsonAsync($"/User/login?useCookies={useCookies.ToString().ToLower()}", model);

    public async Task<HttpResponseMessage> LogoutAsync(bool useCookies = false)
        => await httpClient.PostAsync($"/User/logout?useCookies={useCookies.ToString().ToLower()}", null);

    public async Task<HttpResponseMessage> ForgotPasswordAsync(ForgotPasswordRequest model)
        => await httpClient.PostAsJsonAsync("/User/forgotPassword", model);

    public async Task<HttpResponseMessage> ResetPasswordAsync(ResetPasswordRequest model)
        => await httpClient.PostAsJsonAsync("/User/resetPassword", model);

    public async Task<HttpResponseMessage> ResendConfirmationEmailAsync(ResendConfirmationEmailRequest model)
        => await httpClient.PostAsJsonAsync("/User/resendConfirmationEmail", model);

    // Add more methods as needed for other endpoints
}

// Example request models (adjust namespaces as needed)
public class RegisterRequest
{
    public string Email { get; set; } = default!;
    public string Password { get; set; } = default!;
}

public class LoginRequest
{
    public string Email { get; set; } = default!;
    public string Password { get; set; } = default!;
}

public class ForgotPasswordRequest
{
    public string Email { get; set; } = default!;
}

public class ResetPasswordRequest
{
    public string Email { get; set; } = default!;
    public string ResetCode { get; set; } = default!;
    public string NewPassword { get; set; } = default!;
}

public class ResendConfirmationEmailRequest
{
    public string Email { get; set; } = default!;
}