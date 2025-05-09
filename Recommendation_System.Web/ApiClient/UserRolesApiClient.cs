using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using System.Collections.Generic;

namespace Recommendation_System.Web;

public class UserRolesApiClient(HttpClient httpClient)
{
    public async Task<HttpResponseMessage> GetAllUserRolesAsync()
        => await httpClient.GetAsync("/UserRoles");

    public async Task<HttpResponseMessage> GetUserRolesAsync(string userId)
        => await httpClient.GetAsync($"/UserRoles/{Uri.EscapeDataString(userId)}");

    public async Task<HttpResponseMessage> GetUsersInRoleAsync(string roleId)
        => await httpClient.GetAsync($"/UserRoles/Role/{Uri.EscapeDataString(roleId)}");

    public async Task<HttpResponseMessage> AssignUserRoleAsync(UserRoleRequest model)
        => await httpClient.PostAsJsonAsync("/UserRoles", model);

    public async Task<HttpResponseMessage> RemoveUserRoleAsync(string userId, UserRoleRequest model)
        => await httpClient.SendAsync(new HttpRequestMessage(HttpMethod.Delete, $"/UserRoles/{Uri.EscapeDataString(userId)}") { Content = JsonContent.Create(model) });
}

public class UserRoleRequest
{
    public string UserId { get; set; } = default!;
    public string RoleId { get; set; } = default!;
}
