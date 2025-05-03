using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Recommendation_System.Auth.Models;

public class Cart
{
    [Key]
    public Guid CartId { get; set; }

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    // Owner
    public Guid UserId { get; set; }
    [ForeignKey(nameof(UserId))]
    public User User { get; set; } = null!;

    // Items
    public ICollection<CartItem>? Items { get; set; }
}


