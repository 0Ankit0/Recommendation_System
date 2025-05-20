using Microsoft.EntityFrameworkCore;
using Recommendation_System.Data;
using Recommendation_System.Data.Models;
using Recommendation_System.ServiceDefaults.Infrastructure;

namespace Recommendation_System.ApiService.Routes;

public class Addresses : IEndpoint
{
    public void MapEndpoint(IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/addresses");

        group.MapGet("/", async (AppDbContext db) =>
            await db.Set<Address>().ToListAsync());

        group.MapGet("/{id:int}", async (int id, AppDbContext db) =>
            await db.Set<Address>().FindAsync(id));

        group.MapPost("/", async (AddressRequest req, AppDbContext db) =>
        {
            var entity = new Address
            {
                Street = req.Street,
                City = req.City,
                State = req.State,
                PostalCode = req.PostalCode,
                Country = req.Country,
                UserId = req.UserId
            };
            db.Add(entity);
            await db.SaveChangesAsync();
            return Results.Created($"/api/addresses/{entity.AddressId}", entity);
        });
    }
}
