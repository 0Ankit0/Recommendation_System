// Licensed to the .NET Foundation under one or more agreements.
// The .NET Foundation licenses this file to you under the MIT license.

using System.ComponentModel.DataAnnotations;
using System.Diagnostics;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Security.Claims;
using System.Text;
using System.Text.Encodings.Web;

using Recommendation_System.Auth.Models;

using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.BearerToken;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Http.HttpResults;
using Microsoft.AspNetCore.Http.Metadata;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Identity.Data;
using Microsoft.AspNetCore.WebUtilities;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;

[assembly: InternalsVisibleTo("FutsalApi.Tests")]
namespace Recommendation_System.Auth.Routes;

public class AuthApiEndpointRouteBuilderExtensions 
{
    private readonly EmailAddressAttribute _emailAddressAttribute = new();

    public void MapEndpoint(IEndpointRouteBuilder endpoints)
    {
        ArgumentNullException.ThrowIfNull(endpoints);

        var timeProvider = endpoints.ServiceProvider.GetRequiredService<TimeProvider>();
        var bearerTokenOptions = endpoints.ServiceProvider.GetRequiredService<IOptionsMonitor<BearerTokenOptions>>();
        var emailSender = endpoints.ServiceProvider.GetRequiredService<IEmailSender<User>>();
        var linkGenerator = endpoints.ServiceProvider.GetRequiredService<LinkGenerator>();

       string? confirmEmailEndpointName = null;

        var routeGroup = endpoints.MapGroup("User")
            .WithTags("User");


       
        routeGroup.MapPost("/register", RegisterUser)
        .WithName("RegisterUser")
        .WithSummary("Registers a new user.")
        .WithDescription("Creates a new user account with the provided email and password.")
        .Accepts<RegisterRequest>("application/json")
        .Produces<Ok>(StatusCodes.Status200OK)
        .Produces<ValidationProblem>(StatusCodes.Status400BadRequest)
        .ProducesProblem(StatusCodes.Status500InternalServerError);

        routeGroup.MapPost("/login", LoginUser)
        .WithName("LoginUser")
        .WithSummary("Logs in a user.")
        .WithDescription("Authenticates a user with the provided email and password.")
        .Accepts<LoginRequest>("application/json")
        .Produces<Ok<AccessTokenResponse>>(StatusCodes.Status200OK)
        .Produces<EmptyHttpResult>(StatusCodes.Status204NoContent)
        .ProducesProblem(StatusCodes.Status401Unauthorized)
        .ProducesProblem(StatusCodes.Status500InternalServerError);

        routeGroup.MapGet("/login/google", GoogleLogin)
        .WithName("GoogleLogin")
        .WithSummary("Redirects to Google for authentication.")
        .WithDescription("Redirects the user to Google's OAuth 2.0 login page for authentication.")
        .Produces<RedirectHttpResult>(StatusCodes.Status302Found)
        .ProducesProblem(StatusCodes.Status500InternalServerError);

        routeGroup.MapGet("/auth/google/callback", GoogleCallback)
        .WithName("GoogleCallback")
        .WithSummary("Handles the Google login callback.")
        .WithDescription("Processes the Google login callback and signs in the user.")
        .Produces<RedirectHttpResult>(StatusCodes.Status302Found)
        .ProducesProblem(StatusCodes.Status401Unauthorized)
        .ProducesProblem(StatusCodes.Status400BadRequest)
        .ProducesProblem(StatusCodes.Status500InternalServerError);

        routeGroup.MapPost("/logout", LogoutUser)
        .WithName("LogoutUser")
        .WithSummary("Logs out a user.")
        .WithDescription("Logs out the user and invalidates the authentication cookie or bearer token.")
        .Produces<Ok>(StatusCodes.Status200OK)
        .ProducesProblem(StatusCodes.Status400BadRequest)
        .ProducesProblem(StatusCodes.Status500InternalServerError);

        routeGroup.MapPost("/refresh", RefreshToken)
        .WithName("RefreshToken")
        .WithSummary("Refreshes the access token using the refresh token.")
        .WithDescription("Generates a new access token using the provided refresh token.")
        .Accepts<RefreshRequest>("application/json")
        .Produces<Ok<AccessTokenResponse>>(StatusCodes.Status200OK)
        .Produces<UnauthorizedHttpResult>(StatusCodes.Status401Unauthorized)
        .Produces<SignInHttpResult>(StatusCodes.Status200OK)
        .Produces<ChallengeHttpResult>(StatusCodes.Status401Unauthorized);

        routeGroup.MapGet("/confirmEmail", ConfirmEmail)
        .WithName("ConfirmEmail")
        .WithSummary("Confirms the user's email address.")
        .WithDescription("Confirms the user's email address using the provided user ID and confirmation code.")
        .Produces<ContentHttpResult>(StatusCodes.Status200OK)
        .Produces<UnauthorizedHttpResult>(StatusCodes.Status401Unauthorized)
        .ProducesProblem(StatusCodes.Status500InternalServerError)
        .Add(endpointBuilder =>
        {
            var finalPattern = ((RouteEndpointBuilder)endpointBuilder).RoutePattern.RawText;
            confirmEmailEndpointName = $"{nameof(MapEndpoint)}-{finalPattern}";
            endpointBuilder.Metadata.Add(new EndpointNameMetadata(confirmEmailEndpointName));
        });

        routeGroup.MapPost("/resendConfirmationEmail", ResendConfirmationEmail)
        .WithName("ResendConfirmationEmail")
        .WithSummary("Resends the email confirmation link.")
        .WithDescription("Resends the email confirmation link to the provided email address.")
        .Accepts<ResendConfirmationEmailRequest>("application/json")
        .Produces<Ok>(StatusCodes.Status200OK)
        .ProducesProblem(StatusCodes.Status400BadRequest)
        .ProducesProblem(StatusCodes.Status500InternalServerError);

        routeGroup.MapPost("/forgotPassword", ForgotPassword)
        .WithName("ForgotPassword")
        .WithSummary("Sends a password reset code to the user's email.")
        .WithDescription("Sends a password reset code to the provided email address.")
        .Accepts<ForgotPasswordRequest>("application/json")
        .Produces<Ok>(StatusCodes.Status200OK)
        .Produces<ValidationProblem>(StatusCodes.Status400BadRequest)
        .ProducesProblem(StatusCodes.Status500InternalServerError);

        routeGroup.MapPost("/resetPassword", ResetPassword)
        .WithName("ResetPassword")
        .WithSummary("Resets the user's password.")
        .WithDescription("Resets the user's password using the provided email, reset code, and new password.")
        .Accepts<ResetPasswordRequest>("application/json")
        .Produces<Ok>(StatusCodes.Status200OK)
        .Produces<ValidationProblem>(StatusCodes.Status400BadRequest)
        .ProducesProblem(StatusCodes.Status500InternalServerError);

        var accountGroup = routeGroup.MapGroup("/manage").RequireAuthorization();

        accountGroup.MapPost("/deactivate", DeactivateUser)
        .WithName("DeactivateUser")
        .WithSummary("Deactivate a user.")
        .WithDescription("Deactivate a user account.")
        .Produces<Ok>(StatusCodes.Status200OK)
        .ProducesProblem(StatusCodes.Status400BadRequest)
        .ProducesProblem(StatusCodes.Status404NotFound)
        .ProducesProblem(StatusCodes.Status500InternalServerError);

        accountGroup.MapPost("/revalidate", RevalidateUser)
        .WithName("RevalidateUser")
        .WithSummary("Revalidate a user.")
        .WithDescription("Revalidate a user account.")
        .Produces<Ok>(StatusCodes.Status200OK)
        .ProducesProblem(StatusCodes.Status400BadRequest)
        .ProducesProblem(StatusCodes.Status404NotFound)
        .ProducesProblem(StatusCodes.Status500InternalServerError);

        accountGroup.MapPost("/2fa", TwoFactor)
        .WithName("TwoFactor")
        .WithSummary("Enables or disables two-factor authentication (2FA) for the user.")
        .WithDescription("Enables or disables two-factor authentication (2FA) for the user.")
        .Accepts<TwoFactorRequest>("application/json")
        .Produces<Ok<TwoFactorResponse>>(StatusCodes.Status200OK)
        .Produces<ValidationProblem>(StatusCodes.Status400BadRequest)
        .Produces<NotFound>(StatusCodes.Status404NotFound)
        .ProducesProblem(StatusCodes.Status500InternalServerError);

        accountGroup.MapGet("/info", GetUserInfo)
        .WithName("GetUserInfo")
        .WithSummary("Retrieves the user's information.")
        .WithDescription("Retrieves the user's information, including email and 2FA status.")
        .Produces<Ok<InfoResponse>>(StatusCodes.Status200OK)
        .Produces<ValidationProblem>(StatusCodes.Status400BadRequest)
        .Produces<NotFound>(StatusCodes.Status404NotFound)
        .ProducesProblem(StatusCodes.Status500InternalServerError);

        accountGroup.MapPost("/info", UpdateUserInfo)
        .WithName("UpdateUserInfo")
        .WithSummary("Updates the user's information.")
        .WithDescription("Updates the user's information, including email and password.")
        .Accepts<InfoRequest>("application/json")
        .Produces<Ok<InfoResponse>>(StatusCodes.Status200OK)
        .Produces<ValidationProblem>(StatusCodes.Status400BadRequest)
        .Produces<NotFound>(StatusCodes.Status404NotFound)
        .ProducesProblem(StatusCodes.Status500InternalServerError);
    }

    internal async Task SendConfirmationEmailAsync(
        User user,
        UserManager<User> userManager,
        HttpContext context,
        string email,
        string? confirmEmailEndpointName,
        LinkGenerator linkGenerator,
        IEmailSender<User> emailSender,
        bool isChange = false)
    {
        if (confirmEmailEndpointName is null)
        {
            throw new NotSupportedException("No email confirmation endpoint was registered!");
        }

        var code = isChange
            ? await userManager.GenerateChangeEmailTokenAsync(user, email)
            : await userManager.GenerateEmailConfirmationTokenAsync(user);
        code = WebEncoders.Base64UrlEncode(Encoding.UTF8.GetBytes(code));

        var userId = await userManager.GetUserIdAsync(user);
        var routeValues = new RouteValueDictionary()
        {
            ["userId"] = userId,
            ["code"] = code,
        };

        if (isChange)
        {
            routeValues.Add("changedEmail", email);
        }

        var confirmEmailUrl = linkGenerator.GetUriByName(context, confirmEmailEndpointName, routeValues)
            ?? throw new NotSupportedException($"Could not find endpoint named '{confirmEmailEndpointName}'.");

        await emailSender.SendConfirmationLinkAsync(user, email, HtmlEncoder.Default.Encode(confirmEmailUrl));
    }

    internal async Task<Results<Ok, ValidationProblem>> RegisterUser(
        [FromBody] RegisterRequest registration,
        HttpContext context,
        [FromServices] IServiceProvider sp,
        string? confirmEmailEndpointName,
        LinkGenerator linkGenerator,
        IEmailSender<User> emailSender)
    {
        var userManager = sp.GetRequiredService<UserManager<User>>();
        if (!userManager.SupportsUserEmail)
        {
            throw new NotSupportedException($"{nameof(MapEndpoint)} requires a user store with email support.");
        }
        var userStore = sp.GetRequiredService<IUserStore<User>>();
        var emailStore = (IUserEmailStore<User>)userStore;
        var email = registration.Email;
        if (string.IsNullOrEmpty(email) || !_emailAddressAttribute.IsValid(email))
        {
            return CreateValidationProblem(IdentityResult.Failed(userManager.ErrorDescriber.InvalidEmail(email)));
        }
        var user = new User();
        await userStore.SetUserNameAsync(user, email, CancellationToken.None);
        await emailStore.SetEmailAsync(user, email, CancellationToken.None);
        var result = await userManager.CreateAsync(user, registration.Password);
        if (!result.Succeeded)
        {
            return CreateValidationProblem(result);
        }
        await SendConfirmationEmailAsync(user, userManager, context, email, confirmEmailEndpointName, linkGenerator, emailSender);
        return TypedResults.Ok();
    }

    internal async Task<Results<Ok<AccessTokenResponse>, EmptyHttpResult, ProblemHttpResult>> LoginUser(
        [FromBody] LoginRequest login, [FromQuery] bool? useCookies, [FromQuery] bool? useSessionCookies, [FromServices] IServiceProvider sp)
    {
        var signInManager = sp.GetRequiredService<SignInManager<User>>();
        var useCookieScheme = (useCookies == true) || (useSessionCookies == true);
        var isPersistent = (useCookies == true) && (useSessionCookies != true);
        signInManager.AuthenticationScheme = useCookieScheme ? IdentityConstants.ApplicationScheme : IdentityConstants.BearerScheme;
        var result = await signInManager.PasswordSignInAsync(login.Email, login.Password, isPersistent, lockoutOnFailure: true);
        if (result.RequiresTwoFactor)
        {
            if (!string.IsNullOrEmpty(login.TwoFactorCode))
            {
                result = await signInManager.TwoFactorAuthenticatorSignInAsync(login.TwoFactorCode, isPersistent, rememberClient: isPersistent);
            }
            else if (!string.IsNullOrEmpty(login.TwoFactorRecoveryCode))
            {
                result = await signInManager.TwoFactorRecoveryCodeSignInAsync(login.TwoFactorRecoveryCode);
            }
        }
        if (result.IsLockedOut)
        {
            return TypedResults.Problem("User account locked out.", statusCode: StatusCodes.Status423Locked);
        }
        if (!result.Succeeded)
        {
            return TypedResults.Problem(result.ToString(), statusCode: StatusCodes.Status401Unauthorized);
        }
        return TypedResults.Empty;
    }

    internal async Task<Results<RedirectHttpResult, ProblemHttpResult>> GoogleLogin(
        [FromQuery] string? returnUrl, [FromServices] IServiceProvider sp, HttpContext context)
    {
        var signInManager = sp.GetRequiredService<SignInManager<User>>();
        var properties = signInManager.ConfigureExternalAuthenticationProperties("Google", returnUrl ?? "/auth/google/callback");
        if (properties == null)
        {
            return TypedResults.Problem("Failed to configure Google login.", statusCode: StatusCodes.Status500InternalServerError);
        }
        await context.ChallengeAsync("Google", properties);
        return TypedResults.Redirect(properties.RedirectUri ?? "/");
    }

    internal async Task<Results<RedirectHttpResult, ProblemHttpResult>> GoogleCallback(
        [FromQuery] string? returnUrl, [FromServices] IServiceProvider sp, HttpContext context)
    {
        var signInManager = sp.GetRequiredService<SignInManager<User>>();
        var userManager = sp.GetRequiredService<UserManager<User>>();
        var authenticateResult = await context.AuthenticateAsync("Google");
        if (!authenticateResult.Succeeded)
        {
            return TypedResults.Problem("Google authentication failed.", statusCode: StatusCodes.Status401Unauthorized);
        }
        var email = authenticateResult.Principal?.FindFirstValue(ClaimTypes.Email);
        if (email == null)
        {
            return TypedResults.Problem("Google login did not return an email address.", statusCode: StatusCodes.Status400BadRequest);
        }
        var user = await userManager.FindByEmailAsync(email);
        if (user == null)
        {
            user = new User();
            await userManager.SetUserNameAsync(user, email);
            await userManager.SetEmailAsync(user, email);
            var createResult = await userManager.CreateAsync(user);
            if (!createResult.Succeeded)
            {
                return TypedResults.Problem("Failed to create a new user.", statusCode: StatusCodes.Status500InternalServerError);
            }
        }
        await signInManager.SignInAsync(user, isPersistent: false);
        return TypedResults.Redirect(returnUrl ?? "/");
    }

    internal async Task<Results<Ok, ProblemHttpResult>> LogoutUser(
        [FromQuery] bool? useCookies, [FromQuery] bool? useSessionCookies, [FromServices] IServiceProvider sp)
    {
        var signInManager = sp.GetRequiredService<SignInManager<User>>();
        var useCookieScheme = (useCookies == true) || (useSessionCookies == true);
        signInManager.AuthenticationScheme = useCookieScheme ? IdentityConstants.ApplicationScheme : IdentityConstants.BearerScheme;
        await signInManager.SignOutAsync();
        return TypedResults.Ok();
    }

    internal async Task<Results<Ok<AccessTokenResponse>, UnauthorizedHttpResult, SignInHttpResult, ChallengeHttpResult>> RefreshToken(
        [FromBody] RefreshRequest refreshRequest, [FromServices] IServiceProvider sp)
    {
        var signInManager = sp.GetRequiredService<SignInManager<User>>();
        var bearerTokenOptions = sp.GetRequiredService<IOptionsMonitor<BearerTokenOptions>>();
        var timeProvider = sp.GetRequiredService<TimeProvider>();
        var refreshTokenProtector = bearerTokenOptions.Get(IdentityConstants.BearerScheme).RefreshTokenProtector;
        var refreshTicket = refreshTokenProtector.Unprotect(refreshRequest.RefreshToken);
        if (refreshTicket?.Properties?.ExpiresUtc is not { } expiresUtc ||
            timeProvider.GetUtcNow() >= expiresUtc ||
            await signInManager.ValidateSecurityStampAsync(refreshTicket.Principal) is not User user)
        {
            return TypedResults.Challenge();
        }
        var newPrincipal = await signInManager.CreateUserPrincipalAsync(user);
        return TypedResults.SignIn(newPrincipal, authenticationScheme: IdentityConstants.BearerScheme);
    }

    internal async Task<Results<ContentHttpResult, UnauthorizedHttpResult>> ConfirmEmail(
        [FromQuery] string userId, [FromQuery] string code, [FromQuery] string? changedEmail, [FromServices] IServiceProvider sp)
    {
        var userManager = sp.GetRequiredService<UserManager<User>>();
        if (await userManager.FindByIdAsync(userId) is not { } user)
        {
            return TypedResults.Unauthorized();
        }
        try
        {
            code = Encoding.UTF8.GetString(WebEncoders.Base64UrlDecode(code));
        }
        catch (FormatException)
        {
            return TypedResults.Unauthorized();
        }
        IdentityResult result;
        if (string.IsNullOrEmpty(changedEmail))
        {
            result = await userManager.ConfirmEmailAsync(user, code);
        }
        else
        {
            result = await userManager.ChangeEmailAsync(user, changedEmail, code);
            if (result.Succeeded)
            {
                result = await userManager.SetUserNameAsync(user, changedEmail);
            }
        }
        if (!result.Succeeded)
        {
            return TypedResults.Unauthorized();
        }
        return TypedResults.Text("Thank you for confirming your email.");
    }

    internal async Task<Ok> ResendConfirmationEmail(
        [FromBody] ResendConfirmationEmailRequest resendRequest,
        HttpContext context,
        [FromServices] IServiceProvider sp,
        string? confirmEmailEndpointName,
        LinkGenerator linkGenerator,
        IEmailSender<User> emailSender)
    {
        var userManager = sp.GetRequiredService<UserManager<User>>();
        if (await userManager.FindByEmailAsync(resendRequest.Email) is not { } user)
        {
            return TypedResults.Ok();
        }
        await SendConfirmationEmailAsync(user, userManager, context, resendRequest.Email, confirmEmailEndpointName, linkGenerator, emailSender);
        return TypedResults.Ok();
    }

    internal async Task<Results<Ok, ValidationProblem>> ForgotPassword(
        [FromBody] ForgotPasswordRequest resetRequest, [FromServices] IServiceProvider sp)
    {
        var userManager = sp.GetRequiredService<UserManager<User>>();
        var user = await userManager.FindByEmailAsync(resetRequest.Email);
        if (user is not null && await userManager.IsEmailConfirmedAsync(user))
        {
            var code = await userManager.GeneratePasswordResetTokenAsync(user);
            code = WebEncoders.Base64UrlEncode(Encoding.UTF8.GetBytes(code));
            var emailSender = sp.GetRequiredService<IEmailSender<User>>();
            await emailSender.SendPasswordResetCodeAsync(user, resetRequest.Email, HtmlEncoder.Default.Encode(code));
        }
        return TypedResults.Ok();
    }

    internal async Task<Results<Ok, ValidationProblem>> ResetPassword(
        [FromBody] ResetPasswordRequest resetRequest, [FromServices] IServiceProvider sp)
    {
        var userManager = sp.GetRequiredService<UserManager<User>>();
        var user = await userManager.FindByEmailAsync(resetRequest.Email);
        if (user is null || !(await userManager.IsEmailConfirmedAsync(user)))
        {
            return CreateValidationProblem(IdentityResult.Failed(userManager.ErrorDescriber.InvalidToken()));
        }
        IdentityResult result;
        try
        {
            var code = Encoding.UTF8.GetString(WebEncoders.Base64UrlDecode(resetRequest.ResetCode));
            result = await userManager.ResetPasswordAsync(user, code, resetRequest.NewPassword);
        }
        catch (FormatException)
        {
            result = IdentityResult.Failed(userManager.ErrorDescriber.InvalidToken());
        }
        if (!result.Succeeded)
        {
            return CreateValidationProblem(result);
        }
        return TypedResults.Ok();
    }

    internal async Task<Results<Ok, ProblemHttpResult>> DeactivateUser(
        ClaimsPrincipal claimsPrincipal, [FromServices] IServiceProvider sp)
    {
        var userManager = sp.GetRequiredService<UserManager<User>>();
        if (await userManager.GetUserAsync(claimsPrincipal) is not { } user)
        {
            return TypedResults.Problem("User not found.", statusCode: StatusCodes.Status404NotFound);
        }
        if (user is null || !await userManager.IsEmailConfirmedAsync(user))
        {
            return TypedResults.Problem("User not found or email not confirmed.", statusCode: StatusCodes.Status400BadRequest);
        }
        await userManager.SetLockoutEnabledAsync(user, true);
        var result = await userManager.SetLockoutEndDateAsync(user, DateTimeOffset.UtcNow.AddYears(100));
        if (!result.Succeeded)
        {
            return TypedResults.Problem(result.ToString(), statusCode: StatusCodes.Status500InternalServerError);
        }
        return TypedResults.Ok();
    }

    internal async Task<Results<Ok, ProblemHttpResult>> RevalidateUser(
        ClaimsPrincipal claimsPrincipal, [FromServices] IServiceProvider sp)
    {
        var userManager = sp.GetRequiredService<UserManager<User>>();
        if (await userManager.GetUserAsync(claimsPrincipal) is not { } user)
        {
            return TypedResults.Problem("User not found.", statusCode: StatusCodes.Status404NotFound);
        }
        if (user is null || !await userManager.IsEmailConfirmedAsync(user))
        {
            return TypedResults.Problem("User not found or email not confirmed.", statusCode: StatusCodes.Status400BadRequest);
        }
        var result = await userManager.SetLockoutEndDateAsync(user, null);
        if (!result.Succeeded)
        {
            return TypedResults.Problem(result.ToString(), statusCode: StatusCodes.Status500InternalServerError);
        }
        return TypedResults.Ok();
    }

    internal async Task<Results<Ok<TwoFactorResponse>, ValidationProblem, NotFound>> TwoFactor(
        ClaimsPrincipal claimsPrincipal, [FromBody] TwoFactorRequest tfaRequest, [FromServices] IServiceProvider sp)
    {
        var signInManager = sp.GetRequiredService<SignInManager<User>>();
        var userManager = signInManager.UserManager;
        if (await userManager.GetUserAsync(claimsPrincipal) is not { } user)
        {
            return TypedResults.NotFound();
        }
        if (tfaRequest.Enable == true)
        {
            if (tfaRequest.ResetSharedKey)
            {
                return CreateValidationProblem("CannotResetSharedKeyAndEnable",
                    "Resetting the 2fa shared key must disable 2fa until a 2fa token based on the new shared key is validated.");
            }
            else if (string.IsNullOrEmpty(tfaRequest.TwoFactorCode))
            {
                return CreateValidationProblem("RequiresTwoFactor",
                    "No 2fa token was provided by the request. A valid 2fa token is required to enable 2fa.");
            }
            else if (!await userManager.VerifyTwoFactorTokenAsync(user, userManager.Options.Tokens.AuthenticatorTokenProvider, tfaRequest.TwoFactorCode))
            {
                return CreateValidationProblem("InvalidTwoFactorCode",
                    "The 2fa token provided by the request was invalid. A valid 2fa token is required to enable 2fa.");
            }
            await userManager.SetTwoFactorEnabledAsync(user, true);
        }
        else if (tfaRequest.Enable == false || tfaRequest.ResetSharedKey)
        {
            await userManager.SetTwoFactorEnabledAsync(user, false);
        }
        if (tfaRequest.ResetSharedKey)
        {
            await userManager.ResetAuthenticatorKeyAsync(user);
        }
        string[]? recoveryCodes = null;
        if (tfaRequest.ResetRecoveryCodes || (tfaRequest.Enable == true && await userManager.CountRecoveryCodesAsync(user) == 0))
        {
            var recoveryCodesEnumerable = await userManager.GenerateNewTwoFactorRecoveryCodesAsync(user, 10);
            recoveryCodes = recoveryCodesEnumerable?.ToArray();
        }
        if (tfaRequest.ForgetMachine)
        {
            await signInManager.ForgetTwoFactorClientAsync();
        }
        var key = await userManager.GetAuthenticatorKeyAsync(user);
        if (string.IsNullOrEmpty(key))
        {
            await userManager.ResetAuthenticatorKeyAsync(user);
            key = await userManager.GetAuthenticatorKeyAsync(user);
            if (string.IsNullOrEmpty(key))
            {
                throw new NotSupportedException("The user manager must produce an authenticator key after reset.");
            }
        }
        return TypedResults.Ok(new TwoFactorResponse
        {
            SharedKey = key,
            RecoveryCodes = recoveryCodes,
            RecoveryCodesLeft = recoveryCodes?.Length ?? await userManager.CountRecoveryCodesAsync(user),
            IsTwoFactorEnabled = await userManager.GetTwoFactorEnabledAsync(user),
            IsMachineRemembered = await signInManager.IsTwoFactorClientRememberedAsync(user),
        });
    }

    internal async Task<Results<Ok<InfoResponse>, ValidationProblem, NotFound>> GetUserInfo(
        ClaimsPrincipal claimsPrincipal, [FromServices] IServiceProvider sp)
    {
        var userManager = sp.GetRequiredService<UserManager<User>>();
        if (await userManager.GetUserAsync(claimsPrincipal) is not { } user)
        {
            return TypedResults.NotFound();
        }
        return TypedResults.Ok(await CreateInfoResponseAsync(user, userManager));
    }

    internal async Task<Results<Ok<InfoResponse>, ValidationProblem, NotFound>> UpdateUserInfo(
        ClaimsPrincipal claimsPrincipal,
        [FromBody] InfoRequest infoRequest,
        HttpContext context,
        [FromServices] IServiceProvider sp,
        string? confirmEmailEndpointName,
        LinkGenerator linkGenerator,
        IEmailSender<User> emailSender)
    {
        var userManager = sp.GetRequiredService<UserManager<User>>();
        if (await userManager.GetUserAsync(claimsPrincipal) is not { } user)
        {
            return TypedResults.NotFound();
        }
        if (!string.IsNullOrEmpty(infoRequest.NewEmail) && !_emailAddressAttribute.IsValid(infoRequest.NewEmail))
        {
            return CreateValidationProblem(IdentityResult.Failed(userManager.ErrorDescriber.InvalidEmail(infoRequest.NewEmail)));
        }
        if (!string.IsNullOrEmpty(infoRequest.NewPassword))
        {
            if (string.IsNullOrEmpty(infoRequest.OldPassword))
            {
                return CreateValidationProblem("OldPasswordRequired",
                    "The old password is required to set a new password. If the old password is forgotten, use /resetPassword.");
            }
            var changePasswordResult = await userManager.ChangePasswordAsync(user, infoRequest.OldPassword, infoRequest.NewPassword);
            if (!changePasswordResult.Succeeded)
            {
                return CreateValidationProblem(changePasswordResult);
            }
        }
        if (!string.IsNullOrEmpty(infoRequest.NewEmail))
        {
            var email = await userManager.GetEmailAsync(user);
            if (email != infoRequest.NewEmail)
            {
                await SendConfirmationEmailAsync(user, userManager, context, infoRequest.NewEmail, confirmEmailEndpointName, linkGenerator, emailSender, isChange: true);
            }
        }
        return TypedResults.Ok(await CreateInfoResponseAsync(user, userManager));
    }

    private ValidationProblem CreateValidationProblem(string errorCode, string errorDescription) =>
        TypedResults.ValidationProblem(new Dictionary<string, string[]> {
            { errorCode, [errorDescription] }
        });

    private ValidationProblem CreateValidationProblem(IdentityResult result)
    {
        Debug.Assert(!result.Succeeded);
        var errorDictionary = new Dictionary<string, string[]>(1);

        foreach (var error in result.Errors)
        {
            string[] newDescriptions;

            if (errorDictionary.TryGetValue(error.Code, out var descriptions))
            {
                newDescriptions = new string[descriptions.Length + 1];
                Array.Copy(descriptions, newDescriptions, descriptions.Length);
                newDescriptions[descriptions.Length] = error.Description;
            }
            else
            {
                newDescriptions = [error.Description];
            }

            errorDictionary[error.Code] = newDescriptions;
        }

        return TypedResults.ValidationProblem(errorDictionary);
    }

    private async Task<InfoResponse> CreateInfoResponseAsync(User user, UserManager<User> userManager)
    {
        return new()
        {
            Email = await userManager.GetEmailAsync(user) ?? throw new NotSupportedException("Users must have an email."),
            IsEmailConfirmed = await userManager.IsEmailConfirmedAsync(user),
        };
    }

    private sealed class IdentityEndpointsConventionBuilder(RouteGroupBuilder inner) : IEndpointConventionBuilder
    {
        private IEndpointConventionBuilder InnerAsConventionBuilder => inner;

        public void Add(Action<EndpointBuilder> convention) => InnerAsConventionBuilder.Add(convention);
        public void Finally(Action<EndpointBuilder> finallyConvention) => InnerAsConventionBuilder.Finally(finallyConvention);
    }

    [AttributeUsage(AttributeTargets.Parameter)]
    private sealed class FromBodyAttribute : Attribute, IFromBodyMetadata
    {
    }

    [AttributeUsage(AttributeTargets.Parameter)]
    private sealed class FromServicesAttribute : Attribute, IFromServiceMetadata
    {
    }

    [AttributeUsage(AttributeTargets.Parameter)]
    private sealed class FromQueryAttribute : Attribute, IFromQueryMetadata
    {
        public string? Name => null;
    }
}
