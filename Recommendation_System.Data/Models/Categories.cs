using System;

namespace Recommendation_System.Data.Models;

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

