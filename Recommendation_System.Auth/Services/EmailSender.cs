using System;

using Recommendation_System.Auth.Models;

using Microsoft.AspNetCore.Identity;

namespace Recommendation_System.Auth.Services;

public class EmailSender : IEmailSender<User>
{
    // private readonly ISmtpService _smtpService;
    // public EmailSender(ISmtpService smtpService)
    // {
    //     _smtpService = smtpService;

    // }
    public Task SendConfirmationLinkAsync(User user, string email, string confirmationLink)
    {
        // var subject = "Confirm Your Email";
        // var body = $"Please confirm your email by clicking the following link: {confirmationLink}";
        // _smtpService.SendEmailAsync(email, subject, body);
        return Task.CompletedTask;

    }

    public Task SendPasswordResetLinkAsync(User user, string email, string resetLink)
    {
        // var subject = "Reset Your Password";
        // var body = $"You can reset your password by clicking the following link: {resetLink}";
        // _smtpService.SendEmailAsync(email, subject, body);
        return Task.CompletedTask;
    }

    public Task SendPasswordResetCodeAsync(User user, string email, string resetCode)
    {
        // var subject = "Your Password Reset Code";
        // var body = $"Your password reset code is: {resetCode}";
        // _smtpService.SendEmailAsync(email, subject, body);
        return Task.CompletedTask;
    }
}
