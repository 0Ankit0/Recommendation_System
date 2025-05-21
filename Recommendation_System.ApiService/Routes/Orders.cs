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
            await db.Orders.Include(o => o.OrderItems).Include(o => o.Payment)
                .Select(o => new OrderResponse
                {
                    OrderId = o.OrderId,
                    OrderDate = o.OrderDate,
                    Status = o.Status.ToString(),
                    TotalAmount = o.TotalAmount,
                    UserId = o.UserId,
                    ShippingAddressId = o.ShippingAddressId,
                    OrderItems = o.OrderItems.Select(oi => new OrderItemResponse
                    {
                        OrderItemId = oi.OrderItemId,
                        Quantity = oi.Quantity,
                        UnitPrice = oi.UnitPrice,
                        ProductId = oi.ProductId
                    }).ToList(),
                    Payment = o.Payment != null ? new PaymentResponse
                    {
                        PaymentId = o.Payment.PaymentId,
                        Amount = o.Payment.Amount,
                        Provider = o.Payment.Provider,
                        OrderId = o.Payment.OrderId
                    } : null
                }).ToListAsync());

        group.MapGet("/{id:guid}", async (Guid id, AppDbContext db) =>
            await db.Orders.Include(o => o.OrderItems).Include(o => o.Payment)
                .Where(o => o.OrderId == id)
                .Select(o => new OrderResponse
                {
                    OrderId = o.OrderId,
                    OrderDate = o.OrderDate,
                    Status = o.Status.ToString(),
                    TotalAmount = o.TotalAmount,
                    UserId = o.UserId,
                    ShippingAddressId = o.ShippingAddressId,
                    OrderItems = o.OrderItems.Select(oi => new OrderItemResponse
                    {
                        OrderItemId = oi.OrderItemId,
                        Quantity = oi.Quantity,
                        UnitPrice = oi.UnitPrice,
                        ProductId = oi.ProductId
                    }).ToList(),
                    Payment = o.Payment != null ? new PaymentResponse
                    {
                        PaymentId = o.Payment.PaymentId,
                        Amount = o.Payment.Amount,
                        Provider = o.Payment.Provider,
                        OrderId = o.Payment.OrderId
                    } : null
                }).FirstOrDefaultAsync());

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
            // Return as OrderResponse
            var response = new OrderResponse
            {
                OrderId = entity.OrderId,
                OrderDate = entity.OrderDate,
                Status = entity.Status.ToString(),
                TotalAmount = entity.TotalAmount,
                UserId = entity.UserId,
                ShippingAddressId = entity.ShippingAddressId,
                OrderItems = entity.OrderItems.Select(oi => new OrderItemResponse
                {
                    OrderItemId = oi.OrderItemId,
                    Quantity = oi.Quantity,
                    UnitPrice = oi.UnitPrice,
                    ProductId = oi.ProductId
                }).ToList(),
                Payment = entity.Payment != null ? new PaymentResponse
                {
                    PaymentId = entity.Payment.PaymentId,
                    Amount = entity.Payment.Amount,
                    Provider = entity.Payment.Provider,
                    OrderId = entity.Payment.OrderId
                } : null
            };
            return Results.Created($"/api/orders/{entity.OrderId}", response);
        });

        // --- OrderItems endpoints moved here ---
        group.MapGet("/{orderId:guid}/items", async (Guid orderId, AppDbContext db) =>
            await db.OrderItems.Where(oi => oi.OrderId == orderId)
                .Select(oi => new OrderItemResponse
                {
                    OrderItemId = oi.OrderItemId,
                    Quantity = oi.Quantity,
                    UnitPrice = oi.UnitPrice,
                    ProductId = oi.ProductId
                }).ToListAsync());

        group.MapGet("/{orderId:guid}/items/{itemId:int}", async (Guid orderId, int itemId, AppDbContext db) =>
            await db.OrderItems.Where(oi => oi.OrderId == orderId && oi.OrderItemId == itemId)
                .Select(oi => new OrderItemResponse
                {
                    OrderItemId = oi.OrderItemId,
                    Quantity = oi.Quantity,
                    UnitPrice = oi.UnitPrice,
                    ProductId = oi.ProductId
                }).FirstOrDefaultAsync());

        group.MapPost("/{orderId:guid}/items", async (Guid orderId, OrderItemRequest req, AppDbContext db) =>
        {
            var entity = new OrderItem
            {
                Quantity = req.Quantity,
                UnitPrice = req.UnitPrice,
                OrderId = orderId,
                ProductId = req.ProductId
            };
            db.OrderItems.Add(entity);
            await db.SaveChangesAsync();
            var response = new OrderItemResponse
            {
                OrderItemId = entity.OrderItemId,
                Quantity = entity.Quantity,
                UnitPrice = entity.UnitPrice,
                ProductId = entity.ProductId
            };
            return Results.Created($"/api/orders/{orderId}/items/{entity.OrderItemId}", response);
        });

        group.MapPut("/{orderId:guid}/items/{itemId:int}", async (Guid orderId, int itemId, OrderItemRequest req, AppDbContext db) =>
        {
            var entity = await db.OrderItems.FirstOrDefaultAsync(oi => oi.OrderId == orderId && oi.OrderItemId == itemId);
            if (entity == null) return Results.NotFound();
            entity.Quantity = req.Quantity;
            entity.UnitPrice = req.UnitPrice;
            entity.ProductId = req.ProductId;
            await db.SaveChangesAsync();
            var response = new OrderItemResponse
            {
                OrderItemId = entity.OrderItemId,
                Quantity = entity.Quantity,
                UnitPrice = entity.UnitPrice,
                ProductId = entity.ProductId
            };
            return Results.Ok(response);
        });

        group.MapDelete("/{orderId:guid}/items/{itemId:int}", async (Guid orderId, int itemId, AppDbContext db) =>
        {
            var entity = await db.OrderItems.FirstOrDefaultAsync(oi => oi.OrderId == orderId && oi.OrderItemId == itemId);
            if (entity == null) return Results.NotFound();
            db.OrderItems.Remove(entity);
            await db.SaveChangesAsync();
            return Results.NoContent();
        });
        // --- End OrderItems endpoints ---
    }
}
