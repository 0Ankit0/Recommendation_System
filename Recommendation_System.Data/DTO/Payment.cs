using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

public enum PaymentStatus { Pending, Completed, Failed, Refunded }

public class Payment
{
    [Key]
    public int PaymentId { get; set; }

    public DateTime PaidAt { get; set; } = DateTime.UtcNow;

    [Required]
    public decimal Amount { get; set; }

    public PaymentStatus Status { get; set; } = PaymentStatus.Pending;

    [Required, MaxLength(50)]
    public string Provider { get; set; } = null!;

    // FK to Order
    public Guid OrderId { get; set; }
    [ForeignKey(nameof(OrderId))]
    public Order Order { get; set; } = null!;
}
