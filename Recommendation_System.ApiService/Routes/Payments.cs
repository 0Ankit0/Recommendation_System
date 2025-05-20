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
            await db.Set<Payment>().ToListAsync());

        group.MapGet("/{id:int}", async (int id, AppDbContext db) =>
            await db.Set<Payment>().FindAsync(id));

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
            return Results.Created($"/api/payments/{entity.PaymentId}", entity);
        });
    }
}
