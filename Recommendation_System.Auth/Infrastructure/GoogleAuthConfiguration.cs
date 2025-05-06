using System;
using Microsoft.AspNetCore.Authentication.Google;
using Microsoft.AspNetCore.Authentication;
using Recommendation_System.Auth.Services;

namespace Recommendation_System.Auth.Infrastructure;

public static class GoogleAuthConfiguration
{
    public static AuthenticationBuilder AddGoogleAuthentication(
            this AuthenticationBuilder builder)
    {
        builder.Services.AddScoped<IGeneralSettingsService, GeneralSettingsService>();
        var serviceProvider = builder.Services.BuildServiceProvider();
        var secretRetriever = serviceProvider.GetRequiredService<IGeneralSettingsService>();

        var googleClientId = secretRetriever.GetValueAsync("Google:ClientId").GetAwaiter().GetResult();
        var googleClientSecret = secretRetriever.GetValueAsync("Google:ClientSecret").GetAwaiter().GetResult();

        builder.AddGoogle(googleOptions =>
        {
            googleOptions.ClientId = googleClientId;
            googleOptions.ClientSecret = googleClientSecret;
            googleOptions.CallbackPath = "/auth/google/callback";
        });

        return builder;
    }
}
