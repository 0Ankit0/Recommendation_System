using Microsoft.EntityFrameworkCore;
using Recommendation_System.Data;
using Recommendation_System.Data.Models;
using Recommendation_System.ServiceDefaults.Infrastructure;

namespace Recommendation_System.ApiService.Routes;

public class Products : IEndpoint
{
    public void MapEndpoint(IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/products");

        group.MapGet("/", async (AppDbContext db) =>
            await db.Products.Include(p => p.Images).ToListAsync());

        group.MapGet("/{id:int}", async (int id, AppDbContext db) =>
            await db.Products.Include(p => p.Images).FirstOrDefaultAsync(p => p.ProductId == id));

        group.MapPost("/", async (ProductRequest req, AppDbContext db) =>
        {
            var entity = new Product
            {
                Name = req.Name,
                Description = req.Description,
                Price = req.Price,
                StockQuantity = req.StockQuantity,
                CategoryId = req.CategoryId
            };
            db.Products.Add(entity);
            await db.SaveChangesAsync();
            return Results.Created($"/api/products/{entity.ProductId}", entity);
        });
    }
}
