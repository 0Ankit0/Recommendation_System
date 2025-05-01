using System;
using Recommendation_System.Auth.Models;

using Microsoft.AspNetCore.Authorization;

namespace FutsalApi.ApiService.Infrastructure.Auth;

public class PermissionResourceFilter : IEndpointFilter
{
    private readonly Permissions[] _permissions;
    private readonly Resources _resource;

    public PermissionResourceFilter(Permissions[] permissions, Resources resource)
    {
        _permissions = permissions;
        _resource = resource;
    }

    public async ValueTask<object?> InvokeAsync(EndpointFilterInvocationContext context, EndpointFilterDelegate next)
    {
        var authorizationService = context.HttpContext.RequestServices.GetRequiredService<IAuthorizationService>();
        var user = context.HttpContext.User;

        foreach (var permission in _permissions)
        {
            var requirement = new PermissionResourceRequirement(permission, _resource);
            var result = await authorizationService.AuthorizeAsync(user, null, requirement);
            if (result.Succeeded)
                return await next(context);
        }

        return Results.Forbid();
    }
}
