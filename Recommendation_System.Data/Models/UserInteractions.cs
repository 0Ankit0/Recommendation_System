namespace Recommendation_System.Data.Models;

public class UserInteractionRequest
{
    public string UserId { get; set; } = null!;
    public int ProductId { get; set; }
    public string InteractionType { get; set; } = null!;
    public string? Metadata { get; set; }
}

public class UserInteractionResponse
{
    public int Id { get; set; }
    public string UserId { get; set; } = null!;
    public int ProductId { get; set; }
    public string InteractionType { get; set; } = null!;
    public DateTime InteractionTime { get; set; }
    public string? Metadata { get; set; }
}
