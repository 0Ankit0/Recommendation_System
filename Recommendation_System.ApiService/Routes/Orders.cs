using Microsoft.EntityFrameworkCore;
using Recommendation_System.Data;
using Recommendation_System.Data.Models;
using Recommendation_System.ServiceDefaults.Infrastructure;

namespace Recommendation_System.ApiService.Routes;

public class Orders : IEndpoint
{
    public void MapEndpoint(IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/orders");

        group.MapGet("/", async (AppDbContext db) =>
            await db.Orders.Include(o => o.OrderItems).Include(o => o.Payment).ToListAsync());

        group.MapGet("/{id:guid}", async (Guid id, AppDbContext db) =>
            await db.Orders.Include(o => o.OrderItems).Include(o => o.Payment).FirstOrDefaultAsync(o => o.OrderId == id));

        group.MapPost("/", async (OrderRequest req, AppDbContext db) =>
        {
            var entity = new Order
            {
                UserId = req.UserId,
                TotalAmount = req.TotalAmount,
                ShippingAddressId = req.ShippingAddressId,
                OrderItems = req.OrderItems.Select(oi => new OrderItem
                {
                    Quantity = oi.Quantity,
                    UnitPrice = oi.UnitPrice,
                    ProductId = oi.ProductId
                }).ToList()
            };
            db.Orders.Add(entity);
            await db.SaveChangesAsync();
            return Results.Created($"/api/orders/{entity.OrderId}", entity);
        });
    }
}
