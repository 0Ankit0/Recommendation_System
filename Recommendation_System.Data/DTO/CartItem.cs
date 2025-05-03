using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

public class CartItem
{
    [Key]
    public int CartItemId { get; set; }

    [Required]
    public int Quantity { get; set; }

    // FKs
    public Guid CartId { get; set; }
    [ForeignKey(nameof(CartId))]
    public Cart Cart { get; set; } = null!;

    public int ProductId { get; set; }
    [ForeignKey(nameof(ProductId))]
    public Product Product { get; set; } = null!;
}