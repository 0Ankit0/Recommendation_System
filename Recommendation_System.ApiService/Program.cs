using Microsoft.EntityFrameworkCore;
using Recommendation_System.Auth.Infrastructure;
using Recommendation_System.Data;
using Recommendation_System.ServiceDefaults.Infrastructure;
using Scalar.AspNetCore;

var builder = WebApplication.CreateBuilder(args);

// Add service defaults & Aspire client integrations.
builder.AddServiceDefaults();

//Add postgres db context
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection"),
    b => b.MigrationsAssembly("Recommendation_System.Data")));
//dotnet ef migrations add MigrationName --project Recommendation_System.Data --startup-project Recommendation_System.ApiService
//dotnet ef database update --project Recommendation_System.Data --startup-project Recommendation_System.ApiService

// Add services to the container.
builder.Services.AddProblemDetails();

// Configure JSON serialization to preserve property case
builder.Services.Configure<Microsoft.AspNetCore.Http.Json.JsonOptions>(options =>
{
    options.SerializerOptions.PropertyNamingPolicy = null; // Use PascalCase (default for C# models)
});

// Configure OpenAPI
builder.Services.AddOpenApi(options =>
{
    options.AddDocumentTransformer((document, context, _) =>
    {
        document.Info = new()
        {
            Title = "Recommendation System API",
            Version = "v1",
            Description = """
                Modern API for  product Recommendation according to the user activity.
                """,
            Contact = new()
            {
                Name = "API Support",
                Email = "api@example.com",
                Url = new Uri("https://api.example.com/support")
            }
        };
        return Task.CompletedTask;
    });
});

builder.Services.AddAuthConfig(builder.Configuration);
builder.Services.AddEndpoints(typeof(Program).Assembly);
var app = builder.Build();


// Configure the HTTP request pipeline.
app.UseExceptionHandler();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();

    app.MapGet("/", () => Results.Redirect("/scalar"))
   .ExcludeFromDescription();

    app.MapScalarApiReference();
}
string[] summaries = ["Freezing", "Bracing", "Chilly", "Cool", "Mild", "Warm", "Balmy", "Hot", "Sweltering", "Scorching"];

app.UseAuthConfig(app);
app.MapGet("/weatherforecast", () =>
{
    var forecast = Enumerable.Range(1, 5).Select(index =>
        new WeatherForecast
        (
            DateOnly.FromDateTime(DateTime.Now.AddDays(index)),
            Random.Shared.Next(-20, 55),
            summaries[Random.Shared.Next(summaries.Length)]
        ))
        .ToArray();
    return forecast;
})
.WithName("GetWeatherForecast");

app.MapDefaultEndpoints();
app.MapEndpoints();

app.Run();
record WeatherForecast(DateOnly Date, int TemperatureC, string? Summary)
{
    public int TemperatureF => 32 + (int)(TemperatureC / 0.5556);
}
