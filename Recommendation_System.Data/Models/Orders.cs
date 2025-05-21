namespace Recommendation_System.Data.Models;

public class OrderRequest
{
    public string UserId { get; set; } = null!;
    public decimal TotalAmount { get; set; }
    public int ShippingAddressId { get; set; }
    public List<OrderItemRequest> OrderItems { get; set; } = new();
}

public class OrderResponse
{
    public Guid OrderId { get; set; }
    public DateTime OrderDate { get; set; }
    public string Status { get; set; } = null!;
    public decimal TotalAmount { get; set; }
    public string UserId { get; set; } = null!;
    public int ShippingAddressId { get; set; }
    public List<OrderItemResponse> OrderItems { get; set; } = new();
    public PaymentResponse? Payment { get; set; }
}
