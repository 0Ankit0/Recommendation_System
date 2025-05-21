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

        // This endpoint is now deprecated. All product image operations are handled under /api/products/{productId}/images.
        // Deprecated: Use /api/products/{productId}/images instead. For backward compatibility, return response models.
        group.MapGet("/", async (AppDbContext db) =>
            await db.Set<ProductImage>().AsNoTracking().Select(img => new ProductImageResponse
            {
                ImageId = img.ImageId,
                Url = img.Url,
                IsPrimary = img.IsPrimary,
                ProductId = img.ProductId
            }).ToListAsync());

        group.MapGet("/{id:int}", async (int id, AppDbContext db) =>
            await db.Set<ProductImage>().AsNoTracking().Where(img => img.ImageId == id).Select(img => new ProductImageResponse
            {
                ImageId = img.ImageId,
                Url = img.Url,
                IsPrimary = img.IsPrimary,
                ProductId = img.ProductId
            }).FirstOrDefaultAsync());

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
            var response = new ProductImageResponse
            {
                ImageId = entity.ImageId,
                Url = entity.Url,
                IsPrimary = entity.IsPrimary,
                ProductId = entity.ProductId
            };
            return Results.Created($"/api/productimages/{entity.ImageId}", response);
        });
    }
}
