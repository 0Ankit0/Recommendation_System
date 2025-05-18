using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Recommendation_System.Auth.Models;

public class Address
{
    [Key]
    public int AddressId { get; set; }

    [Required, MaxLength(250)]
    public string Street { get; set; } = null!;

    [Required, MaxLength(100)]
    public string City { get; set; } = null!;

    [Required, MaxLength(100)]
    public string State { get; set; } = null!;

    [Required, MaxLength(20)]
    public string PostalCode { get; set; } = null!;

    [Required, MaxLength(100)]
    public string Country { get; set; } = null!;

    // FK to User
    public required string UserId { get; set; }
    [ForeignKey(nameof(UserId))]
    public User? User { get; set; }
}
