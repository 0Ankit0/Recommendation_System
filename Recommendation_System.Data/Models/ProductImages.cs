namespace Recommendation_System.Data.Models;

public class ProductImageRequest
{
    public string Url { get; set; } = null!;
    public bool IsPrimary { get; set; } = false;
    public int ProductId { get; set; }
}

public class ProductImageResponse
{
    public int ImageId { get; set; }
    public string Url { get; set; } = null!;
    public bool IsPrimary { get; set; }
    public int ProductId { get; set; }
}
