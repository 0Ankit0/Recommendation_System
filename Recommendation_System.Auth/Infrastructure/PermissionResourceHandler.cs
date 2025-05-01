using System;

using Microsoft.AspNetCore.Authorization;

namespace FutsalApi.ApiService.Infrastructure.Auth;

public class PermissionResourceHandler : AuthorizationHandler<PermissionResourceRequirement>
{
    protected override Task HandleRequirementAsync(AuthorizationHandlerContext context, PermissionResourceRequirement requirement)
    {
        var claimValue = $"{requirement.Permission}:{requirement.Resource}";
        if (context.User.HasClaim("Permission", claimValue))
        {
            context.Succeed(requirement);
        }
        return Task.CompletedTask;
    }
}
