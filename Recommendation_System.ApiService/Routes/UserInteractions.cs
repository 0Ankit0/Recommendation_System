using Microsoft.EntityFrameworkCore;
using Recommendation_System.Data;
using Recommendation_System.Data.DTO;
using Recommendation_System.Data.Models;
using Recommendation_System.ServiceDefaults.Infrastructure;

namespace Recommendation_System.ApiService.Routes;

public class UserInteractions : IEndpoint
{
    public void MapEndpoint(IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/userinteractions");

        group.MapGet("/", async (AppDbContext db) =>
            await db.Set<UserInteraction>().ToListAsync());

        group.MapGet("/{id:int}", async (int id, AppDbContext db) =>
            await db.Set<UserInteraction>().FindAsync(id));

        group.MapPost("/", async (UserInteractionRequest req, AppDbContext db) =>
        {
            var entity = new UserInteraction
            {
                UserId = req.UserId,
                ProductId = req.ProductId,
                InteractionType = Enum.Parse<InteractionType>(req.InteractionType),
                Metadata = req.Metadata
            };
            db.Add(entity);
            await db.SaveChangesAsync();
            return Results.Created($"/api/userinteractions/{entity.Id}", entity);
        });
    }
}
