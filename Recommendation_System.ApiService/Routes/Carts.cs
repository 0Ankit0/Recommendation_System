using System;
using Microsoft.EntityFrameworkCore;
using Recommendation_System.Data;
using Recommendation_System.Data.Models;
using Recommendation_System.ServiceDefaults.Infrastructure;

namespace Recommendation_System.ApiService.Routes;

public class CartEndpoints : IEndpoint
{
    public void MapEndpoint(IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/cart");

        // Add item to cart
        group.MapPost("/add", async (AddCartItemRequest req, AppDbContext db) =>
        {
            var cart = await db.Carts
                .Include(c => c.Items)
                .FirstOrDefaultAsync(c => c.UserId == req.UserId);

            if (cart == null)
            {
                cart = new Cart
                {
                    CartId = Guid.NewGuid(),
                    UserId = req.UserId,
                    CreatedAt = DateTime.UtcNow,
                    Items = new List<CartItem>()
                };
                db.Carts.Add(cart);
            }

            var existingItem = cart.Items?.FirstOrDefault(i => i.ProductId == req.ProductId);
            if (existingItem != null)
            {
                existingItem.Quantity += req.Quantity;
            }
            else
            {
                var newItem = new CartItem
                {
                    ProductId = req.ProductId,
                    Quantity = req.Quantity,
                    CartId = cart.CartId
                };
                cart.Items?.Add(newItem);
            }

            await db.SaveChangesAsync();

            // Return a response model
            var response = new CartResponse
            {
                CartId = cart.CartId,
                UserId = cart.UserId,
                CreatedAt = cart.CreatedAt,
                Items = cart.Items?.Select(i => new CartItemResponse
                {
                    ProductId = i.ProductId,
                    Quantity = i.Quantity
                }).ToList() ?? new List<CartItemResponse>()
            };

            return Results.Ok(response);
        });

        // Remove item from cart
        group.MapPost("/remove", async (RemoveCartItemRequest req, AppDbContext db) =>
        {
            var cart = await db.Carts
                .Include(c => c.Items)
                .FirstOrDefaultAsync(c => c.UserId == req.UserId);

            if (cart == null)
                return Results.NotFound("Cart not found");

            var item = cart.Items?.FirstOrDefault(i => i.ProductId == req.ProductId);
            if (item == null)
                return Results.NotFound("Item not found in cart");

            cart.Items?.Remove(item);
            db.CartItems.Remove(item);
            await db.SaveChangesAsync();

            var response = new CartResponse
            {
                CartId = cart.CartId,
                UserId = cart.UserId,
                CreatedAt = cart.CreatedAt,
                Items = cart.Items?.Select(i => new CartItemResponse
                {
                    ProductId = i.ProductId,
                    Quantity = i.Quantity
                }).ToList() ?? new List<CartItemResponse>()
            };


            return Results.Ok(response);
        });
        group.MapPost("/change-quantity", async (AddCartItemRequest req, AppDbContext db) =>
        {
            var cart = await db.Carts
                .Include(c => c.Items)
                .FirstOrDefaultAsync(c => c.UserId == req.UserId);

            if (cart == null)
                return Results.NotFound("Cart not found");

            var item = cart.Items?.FirstOrDefault(i => i.ProductId == req.ProductId);
            if (item == null)
                return Results.NotFound("Item not found in cart");

            if (req.Quantity <= 0)
            {
                cart.Items?.Remove(item);
                db.CartItems.Remove(item);
            }
            else
            {
                item.Quantity = req.Quantity;
            }

            await db.SaveChangesAsync();

            var response = new CartResponse
            {
                CartId = cart.CartId,
                UserId = cart.UserId,
                CreatedAt = cart.CreatedAt,
                Items = cart.Items?.Select(i => new CartItemResponse
                {
                    ProductId = i.ProductId,
                    Quantity = i.Quantity
                }).ToList() ?? new List<CartItemResponse>()
            };

            return Results.Ok(response);
        });
        group.MapGet("/user/{userId}", async (string userId, AppDbContext db) =>
        {
            var cart = await db.Carts.AsNoTracking()
                .Include(c => c.Items)
                .FirstOrDefaultAsync(c => c.UserId == userId);

            if (cart == null)
                return Results.NotFound("Cart not found");

            var response = new CartResponse
            {
                CartId = cart.CartId,
                UserId = cart.UserId,
                CreatedAt = cart.CreatedAt,
                Items = cart.Items?.Select(i => new CartItemResponse
                {
                    ProductId = i.ProductId,
                    Quantity = i.Quantity
                }).ToList() ?? new List<CartItemResponse>()
            };

            return Results.Ok(response);
        });
        // All endpoints already use *Request for input and *Response for output in Carts.cs
    }
}
