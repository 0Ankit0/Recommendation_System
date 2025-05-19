using System;
using Microsoft.AspNetCore.Routing;

namespace Recommendation_System.ServiceDefaults.Infrastructure;

public interface IEndpoint
{
    void MapEndpoint(IEndpointRouteBuilder app);
}
