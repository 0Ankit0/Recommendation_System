using System;
using System.ComponentModel.DataAnnotations;

namespace Recommendation_System.Data.Models;

public class AddCartItemRequest
{
    [Required]
    public string UserId { get; set; } = null!;
    [Required]
    public int ProductId { get; set; }
    public int Quantity { get; set; } = 1;
}

public class RemoveCartItemRequest
{
    [Required]
    public string UserId { get; set; } = null!;
    [Required]
    public int ProductId { get; set; }
}

// Response models
public class CartResponse
{
    public Guid CartId { get; set; }
    public string UserId { get; set; } = null!;
    public DateTime CreatedAt { get; set; }
    public List<CartItemResponse> Items { get; set; } = new();
}

public class CartItemResponse
{
    public int ProductId { get; set; }
    public int Quantity { get; set; }
}
