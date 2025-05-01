using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

using Microsoft.EntityFrameworkCore;

namespace Recommendation_System.Auth.Models;

public class GeneralSetting
{
    [Key]
    [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
    public int Id { get; set; } = 0;
    public string Key { get; set; } = string.Empty;
    public string Value { get; set; } = string.Empty;

}
