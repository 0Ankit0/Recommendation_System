using System;
using System.Text.Json.Serialization;

namespace Recommendation_System.Auth.Models;

public enum ClaimType
{
    Permission,
    Custom

}
public enum Permissions
{
    CanCreate,
    CanEdit,
    CanDelete,
    CanView,
    CanManage
}
public enum Resources
{
    Booking,
    User,
    FutsalGround,
    Role,
    UserRole,
    Image,
    Review,
    GroundClosure,
    Payment,
    Report,
    Notification,
    All
}

public class ClaimModel
{
    //return the type as string

    public ClaimType Type { get; set; }
    //for value make sure the value is using enum Permissions or Resources
    public Permissions Permission { get; set; }
    public Resources Resource { get; set; }
    [JsonIgnore]
    public string Value => $"{Permission}:{Resource}";
}
