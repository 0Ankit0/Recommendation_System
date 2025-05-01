using System;

using Microsoft.AspNetCore.Identity;

namespace Recommendation_System.Auth.Models;

public class User : IdentityUser
{
    public string? ImageUrl { get; set; } = null;

}
