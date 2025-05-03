using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

[Table("Categories")]
public class Category
{
    [Key]
    public int CategoryId { get; set; }

    [Required, MaxLength(150)]
    public string Name { get; set; } = null!;

    public int? ParentCategoryId { get; set; }

    [ForeignKey(nameof(ParentCategoryId))]
    public Category ParentCategory { get; set; } = null!;
    public ICollection<Category>? SubCategories { get; set; }
    public ICollection<Product>? Products { get; set; }
}
