using Microsoft.EntityFrameworkCore;
using Recommendation_System.Data;
using Recommendation_System.Data.Models;
using Recommendation_System.ServiceDefaults.Infrastructure;

namespace Recommendation_System.ApiService.Routes;

public class ProductImages : IEndpoint
{
    public void MapEndpoint(IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/productimages");

        group.MapGet("/", async (AppDbContext db) =>
            await db.Set<ProductImage>().ToListAsync());

        group.MapGet("/{id:int}", async (int id, AppDbContext db) =>
            await db.Set<ProductImage>().FindAsync(id));

        group.MapPost("/", async (ProductImageRequest req, AppDbContext db) =>
        {
            var entity = new ProductImage
            {
                Url = req.Url,
                IsPrimary = req.IsPrimary,
                ProductId = req.ProductId
            };
            db.Add(entity);
            await db.SaveChangesAsync();
            return Results.Created($"/api/productimages/{entity.ImageId}", entity);
        });
    }
}
