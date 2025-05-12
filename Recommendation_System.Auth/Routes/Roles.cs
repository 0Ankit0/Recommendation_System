using System;
using System.Security.Claims;
using Microsoft.AspNetCore.Http.HttpResults;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Recommendation_System.Auth.Models;

namespace Recommendation_System.Auth.Routes;

public class RolesApiEndpoints
{
    public void MapEndpoint(IEndpointRouteBuilder endpoints)
    {
        var routeGroup = endpoints.MapGroup("/Roles")
            .WithTags("Roles")
            .RequireAuthorization();

        // GET: /Roles
        routeGroup.MapGet("/", GetAllRoles)
            .WithName("GetAllRoles")
            .WithSummary("Retrieves all roles.")
            .WithDescription("Returns a list of all roles available in the system.")
            .Produces<IEnumerable<Role>>(StatusCodes.Status200OK)
            .ProducesProblem(StatusCodes.Status500InternalServerError);

        // GET: /Roles/{roleId}
        routeGroup.MapGet("/{roleId}", GetRoleById)
            .WithName("GetRoleById")
            .WithSummary("Retrieves a role by ID.")
            .WithDescription("Returns the role with the specified ID.")
            .Produces<Role>(StatusCodes.Status200OK)
            .ProducesProblem(StatusCodes.Status404NotFound)
            .ProducesProblem(StatusCodes.Status500InternalServerError);

        // POST: /Roles
        routeGroup.MapPost("/", CreateRole)
            .WithName("CreateRole")
            .WithSummary("Creates a new role.")
            .WithDescription("Adds a new role to the system.")
            .Accepts<RoleRequest>("application/json")
            .Produces<Role>(StatusCodes.Status200OK)
            .ProducesProblem(StatusCodes.Status400BadRequest)
            .ProducesProblem(StatusCodes.Status500InternalServerError);

        // PUT: /Roles/{roleId}
        routeGroup.MapPut("/{roleId}", UpdateRole)
            .WithName("UpdateRole")
            .WithSummary("Updates an existing role.")
            .WithDescription("Modifies the details of an existing role identified by its ID.")
            .Accepts<Role>("application/json")
            .Produces<Role>(StatusCodes.Status200OK)
            .ProducesProblem(StatusCodes.Status400BadRequest)
            .ProducesProblem(StatusCodes.Status404NotFound)
            .ProducesProblem(StatusCodes.Status500InternalServerError);

        // DELETE: /Roles/{roleId}
        routeGroup.MapDelete("/{roleId}", DeleteRole)
            .WithName("DeleteRole")
            .WithSummary("Deletes a role.")
            .WithDescription("Removes the role with the specified ID from the system.")
            .Produces(StatusCodes.Status200OK)
            .ProducesProblem(StatusCodes.Status400BadRequest)
            .ProducesProblem(StatusCodes.Status404NotFound)
            .ProducesProblem(StatusCodes.Status500InternalServerError);

        // GET: /Roles/{roleId}/Claims
        routeGroup.MapGet("/{roleId}/Claims", GetRoleClaims)
            .WithName("GetRoleClaims")
            .WithSummary("Retrieves claims for a role.")
            .WithDescription("Returns a list of claims associated with the specified role.")
            .Produces<List<Claim>>(StatusCodes.Status200OK)
            .ProducesProblem(StatusCodes.Status404NotFound)
            .ProducesProblem(StatusCodes.Status500InternalServerError);

        // POST: /Roles/{roleId}/Claims
        routeGroup.MapPost("/{roleId}/Claims", AddRoleClaim)
            .WithName("AddRoleClaim")
            .WithSummary("Adds a claim to a role.")
            .WithDescription("Associates a claim with the specified role.")
            .Produces(StatusCodes.Status200OK)
            .ProducesProblem(StatusCodes.Status400BadRequest)
            .ProducesProblem(StatusCodes.Status404NotFound)
            .ProducesProblem(StatusCodes.Status500InternalServerError);

        // PUT: /Roles/{roleId}/Claims
        routeGroup.MapPut("/{roleId}/Claims", UpdateRoleClaim)
            .WithName("UpdateRoleClaim")
            .WithSummary("Updates a claim for a role.")
            .WithDescription("Modifies an existing claim associated with the specified role.")
            .Accepts<ClaimModel>("application/json")
            .Produces(StatusCodes.Status200OK)
            .ProducesProblem(StatusCodes.Status400BadRequest)
            .ProducesProblem(StatusCodes.Status404NotFound)
            .ProducesProblem(StatusCodes.Status500InternalServerError);

        // DELETE: /Roles/{roleId}/Claims
        routeGroup.MapDelete("/{roleId}/Claims", RemoveRoleClaim)
            .WithName("RemoveRoleClaim")
            .WithSummary("Removes a claim from a role.")
            .WithDescription("Disassociates a claim from the specified role.")
            .Accepts<ClaimModel>("application/json")
            .Produces(StatusCodes.Status200OK)
            .ProducesProblem(StatusCodes.Status400BadRequest)
            .ProducesProblem(StatusCodes.Status404NotFound)
            .ProducesProblem(StatusCodes.Status500InternalServerError);
    }

    internal async Task<Results<Ok<List<Role>>, ProblemHttpResult>> GetAllRoles(
        [FromServices] RoleManager<Role> roleManager)
    {
        try
        {
            var roles = await roleManager.Roles.ToListAsync();
            return TypedResults.Ok(roles);
        }
        catch (Exception ex)
        {
            return TypedResults.Problem($"An error occurred while retrieving roles: {ex.Message}");
        }
    }

    internal async Task<Results<Ok<Role>, ProblemHttpResult>> GetRoleById(
        [FromServices] RoleManager<Role> roleManager,
        string roleId)
    {
        try
        {
            var role = await roleManager.FindByIdAsync(roleId);
            if (role == null)
            {
                return TypedResults.Problem($"Role with ID {roleId} not found.", statusCode: StatusCodes.Status404NotFound);
            }
            return TypedResults.Ok(role);
        }
        catch (Exception ex)
        {
            return TypedResults.Problem($"An error occurred while retrieving the role: {ex.Message}");
        }
    }

    internal async Task<Results<Ok<Role>, ProblemHttpResult>> CreateRole(
        [FromServices] RoleManager<Role> roleManager,
        [FromBody] RoleRequest roleRequest)
    {
        try
        {
            var role = new Role { Name = roleRequest.Name };
            var result = await roleManager.CreateAsync(role);
            if (!result.Succeeded)
            {
                return TypedResults.Problem($"Failed to create role: {string.Join(", ", result.Errors.Select(e => e.Description))}", statusCode: StatusCodes.Status400BadRequest);
            }
            return TypedResults.Ok(role);
        }
        catch (Exception ex)
        {
            return TypedResults.Problem($"An error occurred while creating the role: {ex.Message}");
        }
    }

    internal async Task<Results<Ok<Role>, ProblemHttpResult>> UpdateRole(
        [FromServices] RoleManager<Role> roleManager,
        string roleId,
        [FromBody] Role role)
    {
        try
        {
            var existingRole = await roleManager.FindByIdAsync(roleId);
            if (existingRole == null)
            {
                return TypedResults.Problem($"Role with ID {roleId} not found.", statusCode: StatusCodes.Status404NotFound);
            }

            existingRole.Name = role.Name;
            var result = await roleManager.UpdateAsync(existingRole);
            if (!result.Succeeded)
            {
                return TypedResults.Problem($"Failed to update role: {string.Join(", ", result.Errors.Select(e => e.Description))}", statusCode: StatusCodes.Status400BadRequest);
            }
            return TypedResults.Ok(existingRole);
        }
        catch (Exception ex)
        {
            return TypedResults.Problem($"An error occurred while updating the role: {ex.Message}");
        }
    }

    internal async Task<Results<Ok, ProblemHttpResult, NotFound>> DeleteRole(
        [FromServices] RoleManager<Role> roleManager,
        string roleId)
    {
        try
        {
            var role = await roleManager.FindByIdAsync(roleId);
            if (role == null)
            {
                return TypedResults.Problem($"Role with ID {roleId} not found.", statusCode: StatusCodes.Status404NotFound);
            }

            var result = await roleManager.DeleteAsync(role);
            if (!result.Succeeded)
            {
                return TypedResults.Problem($"Failed to delete role: {string.Join(", ", result.Errors.Select(e => e.Description))}", statusCode: StatusCodes.Status400BadRequest);
            }
            return TypedResults.Ok();
        }
        catch (Exception ex)
        {
            return TypedResults.Problem($"An error occurred while deleting the role: {ex.Message}");
        }
    }

    internal async Task<Results<Ok<List<Claim>>, ProblemHttpResult>> GetRoleClaims(
        [FromServices] RoleManager<Role> roleManager,
        string roleId)
    {
        try
        {
            var role = await roleManager.FindByIdAsync(roleId);
            if (role == null)
            {
                return TypedResults.Problem($"Role with ID {roleId} not found.", statusCode: StatusCodes.Status404NotFound);
            }

            var claims = await roleManager.GetClaimsAsync(role);
            return TypedResults.Ok(claims.ToList());
        }
        catch (Exception ex)
        {
            return TypedResults.Problem($"An error occurred while retrieving claims for the role: {ex.Message}");
        }
    }

    internal async Task<Results<Ok, ProblemHttpResult>> AddRoleClaim(
        ClaimsPrincipal claimsPrincipal,
        [FromServices] UserManager<User> userManager,
        [FromServices] RoleManager<Role> roleManager,
        string roleId,
        [FromBody] ClaimModel claimModel)
    {
        try
        {
            var user = await userManager.GetUserAsync(claimsPrincipal);

            var claim = new Claim(
                claimModel.Type.ToString(),
                 claimModel.Value,
                claimModel.Type == ClaimType.Permission ? "Permission" : "Custom",
                user?.UserName ?? user?.Email,
                "AuthService"
                 );
            var role = await roleManager.FindByIdAsync(roleId);
            if (role == null)
            {
                return TypedResults.Problem($"Role with ID {roleId} not found.", statusCode: StatusCodes.Status404NotFound);
            }

            var result = await roleManager.AddClaimAsync(role, claim);
            if (!result.Succeeded)
            {
                return TypedResults.Problem($"Failed to add claim: {string.Join(", ", result.Errors.Select(e => e.Description))}", statusCode: StatusCodes.Status400BadRequest);
            }
            return TypedResults.Ok();
        }
        catch (Exception ex)
        {
            return TypedResults.Problem($"An error occurred while adding a claim to the role: {ex.Message}");
        }
    }

    internal async Task<Results<Ok, ProblemHttpResult>> UpdateRoleClaim(
        [FromServices] RoleManager<Role> roleManager,
        string roleId,
        [FromBody] ClaimModel claimModel)
    {
        try
        {
            var claim = new Claim(claimModel.Type.ToString(), claimModel.Value);

            var role = await roleManager.FindByIdAsync(roleId);
            if (role == null)
            {
                return TypedResults.Problem($"Role with ID {roleId} not found.", statusCode: StatusCodes.Status404NotFound);
            }

            var existingClaims = await roleManager.GetClaimsAsync(role);
            if (existingClaims.Any(c => c.Type == claim.Type))
            {
                var oldClaim = existingClaims.First(c => c.Type == claim.Type);
                var removeResult = await roleManager.RemoveClaimAsync(role, oldClaim);
                if (!removeResult.Succeeded)
                {
                    return TypedResults.Problem($"Failed to remove old claim: {string.Join(", ", removeResult.Errors.Select(e => e.Description))}", statusCode: StatusCodes.Status400BadRequest);
                }
            }

            var addResult = await roleManager.AddClaimAsync(role, claim);
            if (!addResult.Succeeded)
            {
                return TypedResults.Problem($"Failed to add new claim: {string.Join(", ", addResult.Errors.Select(e => e.Description))}", statusCode: StatusCodes.Status400BadRequest);
            }
            return TypedResults.Ok();
        }
        catch (Exception ex)
        {
            return TypedResults.Problem($"An error occurred while updating a claim for the role: {ex.Message}");
        }
    }

    internal async Task<Results<Ok, ProblemHttpResult>> RemoveRoleClaim(
        [FromServices] RoleManager<Role> roleManager,
        string roleId,
        [FromBody] ClaimModel claimModel)
    {
        try
        {
            var role = await roleManager.FindByIdAsync(roleId);
            if (role == null)
            {
                return TypedResults.Problem($"Role with ID {roleId} not found.", statusCode: StatusCodes.Status404NotFound);
            }

            var claim = new Claim(claimModel.Type.ToString(), claimModel.Value);

            var result = await roleManager.RemoveClaimAsync(role, claim);
            if (!result.Succeeded)
            {
                return TypedResults.Problem($"Failed to remove claim: {string.Join(", ", result.Errors.Select(e => e.Description))}", statusCode: StatusCodes.Status400BadRequest);
            }
            return TypedResults.Ok();
        }
        catch (Exception ex)
        {
            return TypedResults.Problem($"An error occurred while removing a claim from the role: {ex.Message}");
        }
    }
}
