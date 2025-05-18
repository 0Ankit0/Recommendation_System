using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Recommendation_System.Auth.Models;

public enum OrderStatus { Pending, Processing, Shipped, Delivered, Cancelled }

public class Order
{
    [Key]
    public Guid OrderId { get; set; }

    public DateTime OrderDate { get; set; } = DateTime.UtcNow;

    public OrderStatus Status { get; set; } = OrderStatus.Pending;

    [Required]
    public decimal TotalAmount { get; set; }

    // FKs
    public required string UserId { get; set; }
    [ForeignKey(nameof(UserId))]
    public User User { get; set; } = null!;

    public int ShippingAddressId { get; set; }
    [ForeignKey(nameof(ShippingAddressId))]
    public Address ShippingAddress { get; set; } = null!;

    // Navigation
    public ICollection<OrderItem> OrderItems { get; set; } = new List<OrderItem>();
    public Payment? Payment { get; set; }
}
