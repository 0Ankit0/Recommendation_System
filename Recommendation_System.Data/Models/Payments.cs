namespace Recommendation_System.Data.Models;

public class PaymentRequest
{
    public decimal Amount { get; set; }
    public string Provider { get; set; } = null!;
    public Guid OrderId { get; set; }
}

public class PaymentResponse
{
    public int PaymentId { get; set; }
    public DateTime PaidAt { get; set; }
    public decimal Amount { get; set; }
    public string Status { get; set; } = null!;
    public string Provider { get; set; } = null!;
    public Guid OrderId { get; set; }
}
