using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

public class ProductImage
{
    [Key]
    public int ImageId { get; set; }

    [Required, MaxLength(500)]
    public string Url { get; set; } = null!;

    public bool IsPrimary { get; set; } = false;

    // FK to Product
    public int ProductId { get; set; }
    [ForeignKey(nameof(ProductId))]
    public Product Product { get; set; } = null!;
}
