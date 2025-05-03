using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

public class OrderItem
{
    [Key]
    public int OrderItemId { get; set; }

    [Required]
    public int Quantity { get; set; }

    [Required, Column(TypeName = "decimal(18,2)")]
    public decimal UnitPrice { get; set; }

    // FKs
    public Guid OrderId { get; set; }
    [ForeignKey(nameof(OrderId))]
    public Order Order { get; set; } = null!;

    public int ProductId { get; set; }
    [ForeignKey(nameof(ProductId))]
    public Product Product { get; set; } = null!;
}
