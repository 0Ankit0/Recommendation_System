using Microsoft.EntityFrameworkCore;
using Recommendation_System.Data;
using Recommendation_System.Data.Models;
using Recommendation_System.ServiceDefaults.Infrastructure;

namespace Recommendation_System.ApiService.Routes;

public class OrderItems : IEndpoint
{
    public void MapEndpoint(IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/orderitems");

        group.MapGet("/", async (AppDbContext db) =>
            await db.Set<OrderItem>().ToListAsync());

        group.MapGet("/{id:int}", async (int id, AppDbContext db) =>
            await db.Set<OrderItem>().FindAsync(id));

        group.MapPost("/", async (OrderItemRequest req, AppDbContext db) =>
        {
            var entity = new OrderItem
            {
                Quantity = req.Quantity,
                UnitPrice = req.UnitPrice,
                OrderId = req.OrderId,
                ProductId = req.ProductId
            };
            db.Add(entity);
            await db.SaveChangesAsync();
            return Results.Created($"/api/orderitems/{entity.OrderItemId}", entity);
        });
    }
}
