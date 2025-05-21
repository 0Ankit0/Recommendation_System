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
            await db.Set<UserInteraction>().AsNoTracking().Select(ui => new UserInteractionResponse
            {
                Id = ui.Id,
                UserId = ui.UserId,
                ProductId = ui.ProductId,
                InteractionType = ui.InteractionType.ToString(),
                Metadata = ui.Metadata
            }).ToListAsync());

        group.MapGet("/{id:int}", async (int id, AppDbContext db) =>
            await db.Set<UserInteraction>().AsNoTracking().Where(ui => ui.Id == id).Select(ui => new UserInteractionResponse
            {
                Id = ui.Id,
                UserId = ui.UserId,
                ProductId = ui.ProductId,
                InteractionType = ui.InteractionType.ToString(),
                Metadata = ui.Metadata
            }).FirstOrDefaultAsync());

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
            var response = new UserInteractionResponse
            {
                Id = entity.Id,
                UserId = entity.UserId,
                ProductId = entity.ProductId,
                InteractionType = entity.InteractionType.ToString(),
                Metadata = entity.Metadata
            };
            return Results.Created($"/api/userinteractions/{entity.Id}", response);
        });
    }
}
