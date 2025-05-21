using Microsoft.EntityFrameworkCore;
using Recommendation_System.Data;
using Recommendation_System.Data.Models;
using Recommendation_System.ServiceDefaults.Infrastructure;

namespace Recommendation_System.ApiService.Routes;

public class Payments : IEndpoint
{
    public void MapEndpoint(IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/payments");

        group.MapGet("/", async (AppDbContext db) =>
            await db.Set<Payment>().AsNoTracking().Select(p => new PaymentResponse
            {
                PaymentId = p.PaymentId,
                Amount = p.Amount,
                Provider = p.Provider,
                OrderId = p.OrderId
            }).ToListAsync());

        group.MapGet("/{id:int}", async (int id, AppDbContext db) =>
            await db.Set<Payment>().AsNoTracking().Where(p => p.PaymentId == id).Select(p => new PaymentResponse
            {
                PaymentId = p.PaymentId,
                Amount = p.Amount,
                Provider = p.Provider,
                OrderId = p.OrderId
            }).FirstOrDefaultAsync());

        group.MapPost("/", async (PaymentRequest req, AppDbContext db) =>
        {
            var entity = new Payment
            {
                Amount = req.Amount,
                Provider = req.Provider,
                OrderId = req.OrderId
            };
            db.Add(entity);
            await db.SaveChangesAsync();
            var response = new PaymentResponse
            {
                PaymentId = entity.PaymentId,
                Amount = entity.Amount,
                Provider = entity.Provider,
                OrderId = entity.OrderId
            };
            return Results.Created($"/api/payments/{entity.PaymentId}", response);
        });
    }
}
