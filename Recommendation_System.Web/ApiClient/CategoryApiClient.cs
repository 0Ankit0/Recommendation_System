using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using System.Collections.Generic;

namespace Recommendation_System.Web;

public class CategoryApiClient(HttpClient httpClient)
{
    public async Task<List<CategoryResponse>?> GetAllAsync()
        => await httpClient.GetFromJsonAsync<List<CategoryResponse>>("/api/categories");

    public async Task<CategoryResponse?> GetByIdAsync(int id)
        => await httpClient.GetFromJsonAsync<CategoryResponse>($"/api/categories/{id}");

    public async Task<HttpResponseMessage> CreateAsync(CategoryRequest model)
        => await httpClient.PostAsJsonAsync("/api/categories", model);

    public async Task<HttpResponseMessage> UpdateAsync(int id, CategoryRequest model)
        => await httpClient.PutAsJsonAsync($"/api/categories/{id}", model);

    public async Task<HttpResponseMessage> DeleteAsync(int id)
        => await httpClient.DeleteAsync($"/api/categories/{id}");
}
public class CategoryRequest
{
    public string Name { get; set; } = null!;
    public int? ParentCategoryId { get; set; }
}
public class CategoryResponse
{
    public int Id { get; set; }
    public string Name { get; set; } = null!;
    public List<CategoryResponse>? SubCategories { get; set; }
}