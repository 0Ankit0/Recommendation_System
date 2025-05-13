using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.BearerToken;
using System.Net.Http;
using System.Net.Http.Json;
using System.Security.Claims;
using System.Text.Json;
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

    public async Task<HttpResponseMessage> GoogleLoginAsync(string? returnUrl = null)
        => await httpClient.GetAsync($"/User/login/google{(string.IsNullOrEmpty(returnUrl) ? string.Empty : $"?returnUrl={Uri.EscapeDataString(returnUrl)}")}");

    public async Task<HttpResponseMessage> GoogleCallbackAsync(string? returnUrl = null)
        => await httpClient.GetAsync($"/User/auth/google/callback{(string.IsNullOrEmpty(returnUrl) ? string.Empty : $"?returnUrl={Uri.EscapeDataString(returnUrl)}")}");

    public async Task<HttpResponseMessage> RefreshTokenAsync(RefreshRequest model)
        => await httpClient.PostAsJsonAsync("/User/refresh", model);

    public async Task<HttpResponseMessage> ConfirmEmailAsync(string userId, string code, string? changedEmail = null)
    {
        var url = $"/User/confirmEmail?userId={Uri.EscapeDataString(userId)}&code={Uri.EscapeDataString(code)}";
        if (!string.IsNullOrEmpty(changedEmail))
            url += $"&changedEmail={Uri.EscapeDataString(changedEmail)}";
        return await httpClient.GetAsync(url);
    }

    public async Task<HttpResponseMessage> DeactivateUserAsync()
        => await httpClient.PostAsync("/User/manage/deactivate", null);

    public async Task<HttpResponseMessage> RevalidateUserAsync()
        => await httpClient.PostAsync("/User/manage/revalidate", null);

    public async Task<HttpResponseMessage> TwoFactorAsync(TwoFactorRequest model)
        => await httpClient.PostAsJsonAsync("/User/manage/2fa", model);

    public async Task<HttpResponseMessage> GetUserInfoAsync()
        => await httpClient.GetAsync("/User/manage/info");

    public async Task<HttpResponseMessage> UpdateUserInfoAsync(InfoRequest model)
        => await httpClient.PostAsJsonAsync("/User/manage/info", model);

    public async Task<HttpResponseMessage> VerifyResetCodeAsync(VerifyResetCodeRequest model)
        => await httpClient.PostAsJsonAsync("/User/verifyResetCode", model);

    public async Task<HttpResponseMessage> SendRevalidateEmailAsync(ResendConfirmationEmailRequest model)
        => await httpClient.PostAsJsonAsync("/User/manage/sendRevalidateEmail", model);

    public async Task<HttpResponseMessage> RevalidateUserByLinkAsync(string userId, string code)
        => await httpClient.GetAsync($"/User/manage/revalidate?userId={Uri.EscapeDataString(userId)}&code={Uri.EscapeDataString(code)}");

    public async Task<HttpResponseMessage> GenerateTwoFactorSetupCodeAsync()
        => await httpClient.GetAsync("/User/manage/setup2fa");
}

public class RegisterRequest
{
    public string Email { get; set; } = default!;
    public string Password { get; set; } = default!;
}

public class LoginRequest
{
    public string Email { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
    public string? TwoFactorCode { get; set; }
    public string? TwoFactorRecoveryCode { get; set; }
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

public class RefreshRequest
{
    public string RefreshToken { get; set; } = default!;
}

public class TwoFactorRequest
{
    public bool? Enable { get; set; }
    public bool ResetSharedKey { get; set; }
    public string? TwoFactorCode { get; set; }
    public string? TwoFactorRecoveryCode { get; set; }
    public bool ResetRecoveryCodes { get; set; }
    public bool ForgetMachine { get; set; }
}

public class InfoRequest
{
    public string? NewEmail { get; set; }
    public string? OldPassword { get; set; }
    public string? NewPassword { get; set; }
}

public class VerifyResetCodeRequest
{
    public string Email { get; set; } = default!;
    public string ResetCode { get; set; } = default!;
}