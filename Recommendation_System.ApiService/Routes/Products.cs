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
            await db.Products.AsNoTracking().Include(p => p.Images)
                .Select(p => new ProductResponse
                {
                    ProductId = p.ProductId,
                    Name = p.Name,
                    Description = p.Description,
                    Price = p.Price,
                    StockQuantity = p.StockQuantity,
                    CreatedAt = p.CreatedAt,
                    CategoryId = p.CategoryId,
                    Images = p.Images != null ? p.Images.Select(img => new ProductImageResponse
                    {
                        ImageId = img.ImageId,
                        Url = img.Url,
                        IsPrimary = img.IsPrimary,
                        ProductId = img.ProductId
                    }).ToList() : new List<ProductImageResponse>()
                }).ToListAsync());

        group.MapGet("/{id:int}", async (int id, AppDbContext db) =>
            await db.Products.AsNoTracking().Include(p => p.Images)
                .Where(p => p.ProductId == id)
                .Select(p => new ProductResponse
                {
                    ProductId = p.ProductId,
                    Name = p.Name,
                    Description = p.Description,
                    Price = p.Price,
                    StockQuantity = p.StockQuantity,
                    CreatedAt = p.CreatedAt,
                    CategoryId = p.CategoryId,
                    Images = p.Images != null ? p.Images.Select(img => new ProductImageResponse
                    {
                        ImageId = img.ImageId,
                        Url = img.Url,
                        IsPrimary = img.IsPrimary,
                        ProductId = img.ProductId
                    }).ToList() : new List<ProductImageResponse>()
                }).FirstOrDefaultAsync());

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
            var response = new ProductResponse
            {
                ProductId = entity.ProductId,
                Name = entity.Name,
                Description = entity.Description,
                Price = entity.Price,
                StockQuantity = entity.StockQuantity,
                CreatedAt = entity.CreatedAt,
                CategoryId = entity.CategoryId,
                Images = new List<ProductImageResponse>()
            };
            return Results.Created($"/api/products/{entity.ProductId}", response);
        });

        group.MapGet("/{productId:int}/images", async (int productId, AppDbContext db) =>
            await db.ProductImages.Where(img => img.ProductId == productId)
                .Select(img => new ProductImageResponse
                {
                    ImageId = img.ImageId,
                    Url = img.Url,
                    IsPrimary = img.IsPrimary,
                    ProductId = img.ProductId
                }).ToListAsync());

        group.MapGet("/{productId:int}/images/{imageId:int}", async (int productId, int imageId, AppDbContext db) =>
            await db.ProductImages.Where(img => img.ProductId == productId && img.ImageId == imageId)
                .Select(img => new ProductImageResponse
                {
                    ImageId = img.ImageId,
                    Url = img.Url,
                    IsPrimary = img.IsPrimary,
                    ProductId = img.ProductId
                }).FirstOrDefaultAsync());

        group.MapPost("/{productId:int}/images", async (int productId, ProductImageRequest req, AppDbContext db) =>
        {
            var entity = new ProductImage
            {
                Url = req.Url,
                IsPrimary = req.IsPrimary,
                ProductId = productId
            };
            db.ProductImages.Add(entity);
            await db.SaveChangesAsync();
            var response = new ProductImageResponse
            {
                ImageId = entity.ImageId,
                Url = entity.Url,
                IsPrimary = entity.IsPrimary,
                ProductId = entity.ProductId
            };
            return Results.Created($"/api/products/{productId}/images/{entity.ImageId}", response);
        });

        group.MapPut("/{productId:int}/images/{imageId:int}", async (int productId, int imageId, ProductImageRequest req, AppDbContext db) =>
        {
            var entity = await db.ProductImages.FirstOrDefaultAsync(img => img.ProductId == productId && img.ImageId == imageId);
            if (entity == null) return Results.NotFound();
            entity.Url = req.Url;
            entity.IsPrimary = req.IsPrimary;
            await db.SaveChangesAsync();
            var response = new ProductImageResponse
            {
                ImageId = entity.ImageId,
                Url = entity.Url,
                IsPrimary = entity.IsPrimary,
                ProductId = entity.ProductId
            };
            return Results.Ok(response);
        });

        group.MapDelete("/{productId:int}/images/{imageId:int}", async (int productId, int imageId, AppDbContext db) =>
        {
            var entity = await db.ProductImages.FirstOrDefaultAsync(img => img.ProductId == productId && img.ImageId == imageId);
            if (entity == null) return Results.NotFound();
            db.ProductImages.Remove(entity);
            await db.SaveChangesAsync();
            return Results.NoContent();
        });
    }
}
