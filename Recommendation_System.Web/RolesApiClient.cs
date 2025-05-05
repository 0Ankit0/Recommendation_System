using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using System.Collections.Generic;

namespace Recommendation_System.Web;

public class RolesApiClient(HttpClient httpClient)
{
    public async Task<HttpResponseMessage> GetAllRolesAsync()
        => await httpClient.GetAsync("/Roles");

    public async Task<HttpResponseMessage> GetRoleByIdAsync(string roleId)
        => await httpClient.GetAsync($"/Roles/{Uri.EscapeDataString(roleId)}");

    public async Task<HttpResponseMessage> CreateRoleAsync(RoleRequest model)
        => await httpClient.PostAsJsonAsync("/Roles", model);

    public async Task<HttpResponseMessage> UpdateRoleAsync(string roleId, RoleRequest model)
        => await httpClient.PutAsJsonAsync($"/Roles/{Uri.EscapeDataString(roleId)}", model);

    public async Task<HttpResponseMessage> DeleteRoleAsync(string roleId)
        => await httpClient.DeleteAsync($"/Roles/{Uri.EscapeDataString(roleId)}");

    public async Task<HttpResponseMessage> GetRoleClaimsAsync(string roleId)
        => await httpClient.GetAsync($"/Roles/{Uri.EscapeDataString(roleId)}/Claims");

    public async Task<HttpResponseMessage> AddRoleClaimAsync(string roleId, ClaimModel model)
        => await httpClient.PostAsJsonAsync($"/Roles/{Uri.EscapeDataString(roleId)}/Claims", model);

    public async Task<HttpResponseMessage> UpdateRoleClaimAsync(string roleId, ClaimModel model)
        => await httpClient.PutAsJsonAsync($"/Roles/{Uri.EscapeDataString(roleId)}/Claims", model);

    public async Task<HttpResponseMessage> RemoveRoleClaimAsync(string roleId, ClaimModel model)
        => await httpClient.SendAsync(new HttpRequestMessage(HttpMethod.Delete, $"/Roles/{Uri.EscapeDataString(roleId)}/Claims") { Content = JsonContent.Create(model) });
}

public class RoleRequest
{
    public string? Name { get; set; }
}

public class ClaimModel
{
    public string Type { get; set; } = default!;
    public string Value { get; set; } = default!;
}
