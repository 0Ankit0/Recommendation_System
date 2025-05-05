using System;

namespace Recommendation_System.Data.DTO;
public enum InteractionType
{
    View,
    Click,
    AddToCart,
    Purchase,
    Search,
    Review
}

public class UserInteraction
{

    public int Id { get; set; }
    public string UserId { get; set; } = null!;
    public int ProductId { get; set; }
    public InteractionType InteractionType { get; set; }
    public DateTime InteractionTime { get; set; } = DateTime.UtcNow;
    public string? Metadata { get; set; }
    public float[]? Embedding { get; set; }
}
