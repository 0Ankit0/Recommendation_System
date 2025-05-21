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
            await db.Set<Address>().AsNoTracking().Select(a => new AddressResponse
            {
                AddressId = a.AddressId,
                Street = a.Street,
                City = a.City,
                State = a.State,
                PostalCode = a.PostalCode,
                Country = a.Country,
                UserId = a.UserId
            }).ToListAsync());

        group.MapGet("/{id:int}", async (int id, AppDbContext db) =>
            await db.Set<Address>().AsNoTracking().Where(a => a.AddressId == id).Select(a => new AddressResponse
            {
                AddressId = a.AddressId,
                Street = a.Street,
                City = a.City,
                State = a.State,
                PostalCode = a.PostalCode,
                Country = a.Country,
                UserId = a.UserId
            }).FirstOrDefaultAsync());

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
            var response = new AddressResponse
            {
                AddressId = entity.AddressId,
                Street = entity.Street,
                City = entity.City,
                State = entity.State,
                PostalCode = entity.PostalCode,
                Country = entity.Country,
                UserId = entity.UserId
            };
            return Results.Created($"/api/addresses/{entity.AddressId}", response);
        });
    }
}
