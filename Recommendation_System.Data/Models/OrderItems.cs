namespace Recommendation_System.Data.Models;

public class OrderItemRequest
{
    public int Quantity { get; set; }
    public decimal UnitPrice { get; set; }
    public Guid OrderId { get; set; }
    public int ProductId { get; set; }
}

public class OrderItemResponse
{
    public int OrderItemId { get; set; }
    public int Quantity { get; set; }
    public decimal UnitPrice { get; set; }
    public Guid OrderId { get; set; }
    public int ProductId { get; set; }
}
