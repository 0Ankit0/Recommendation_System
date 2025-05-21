using System;
using Microsoft.EntityFrameworkCore;
using Recommendation_System.Data;
using Recommendation_System.Data.Models;
using Recommendation_System.ServiceDefaults.Infrastructure;
using System.Linq;

namespace Recommendation_System.ApiService.Routes;

public class Categories : IEndpoint
{
    public void MapEndpoint(IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/categories");

        // Get all categories (with subcategories, no ParentCategoryId in response)
        group.MapGet("/", async (AppDbContext db) =>
            await db.Categories.AsNoTracking()
                .Where(c => c.ParentCategoryId == null)
                .Select(c => new CategoryResponse
                {
                    Id = c.CategoryId,
                    Name = c.Name,
                    SubCategories = db.Categories
                        .Where(sub => sub.ParentCategoryId == c.CategoryId)
                        .Select(sub => new CategoryResponse
                        {
                            Id = sub.CategoryId,
                            Name = sub.Name,
                            SubCategories = new List<CategoryResponse>()
                        }).ToList()
                })
                .ToListAsync());

        // Get category by id (with subcategories, no ParentCategoryId in response)
        group.MapGet("/{id:int}", async (int id, AppDbContext db) =>
            await db.Categories.AsNoTracking()
                .Where(c => c.CategoryId == id)
                .Select(c => new CategoryResponse
                {
                    Id = c.CategoryId,
                    Name = c.Name,
                    SubCategories = db.Categories
                        .Where(sub => sub.ParentCategoryId == c.CategoryId)
                        .Select(sub => new CategoryResponse
                        {
                            Id = sub.CategoryId,
                            Name = sub.Name,
                            SubCategories = new List<CategoryResponse>()
                        }).ToList()
                })
                .FirstOrDefaultAsync() is CategoryResponse cat
                ? Results.Ok(cat)
                : Results.NotFound());

        // Create category
        group.MapPost("/", async (CategoryRequest dto, AppDbContext db) =>
        {
            var newCategory = new Category
            {
                Name = dto.Name,
                ParentCategoryId = dto.ParentCategoryId
            };
            db.Categories.Add(newCategory);
            await db.SaveChangesAsync();
            var result = new CategoryResponse
            {
                Id = newCategory.CategoryId,
                Name = newCategory.Name,
                SubCategories = new List<CategoryResponse>()
            };
            return Results.Created($"/api/categories/{result.Id}", result);
        });

        // Update category
        group.MapPut("/{id:int}", async (int id, CategoryRequest dto, AppDbContext db) =>
        {
            var category = await db.Categories.FindAsync(id);
            if (category is null)
                return Results.NotFound();

            category.Name = dto.Name;
            category.ParentCategoryId = dto.ParentCategoryId;
            await db.SaveChangesAsync();

            var result = new CategoryResponse
            {
                Id = category.CategoryId,
                Name = category.Name,
                SubCategories = db.Categories
                    .Where(sub => sub.ParentCategoryId == category.CategoryId)
                    .Select(sub => new CategoryResponse
                    {
                        Id = sub.CategoryId,
                        Name = sub.Name,
                        SubCategories = new List<CategoryResponse>()
                    }).ToList()
            };
            return Results.Ok(result);
        });

        // Delete category
        group.MapDelete("/{id:int}", async (int id, AppDbContext db) =>
        {
            var category = await db.Categories.FindAsync(id);
            if (category is null)
                return Results.NotFound();

            db.Categories.Remove(category);
            await db.SaveChangesAsync();
            return Results.NoContent();
        });
    }

}
