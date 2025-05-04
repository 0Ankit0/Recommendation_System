using System;

namespace Recommendation_System.Web;

using System.Reflection;
using Microsoft.Extensions.DependencyInjection;
using System.Net.Http;

public static class ServiceCollectionExtensions
{
    public static void AddClients(this IServiceCollection services)
    {
        var apiBaseAddress = new Uri("https://apiservice");

        // Register all classes with a constructor that takes HttpClient
        var apiClientTypes = Assembly.GetExecutingAssembly()
            .GetTypes()
            .Where(t =>
                t.IsClass &&
                !t.IsAbstract &&
                t.GetConstructors().Any(ctor =>
                    {
                        var parameters = ctor.GetParameters();
                        return parameters.Length == 1 && parameters[0].ParameterType == typeof(HttpClient);
                    }
                )
            );

        foreach (var clientType in apiClientTypes)
        {
            var method = typeof(HttpClientFactoryServiceCollectionExtensions)
                .GetMethods()
                .First(m =>
                    m.Name == "AddHttpClient"
                    && m.IsGenericMethodDefinition
                    && m.GetGenericArguments().Length == 1
                    && m.GetParameters().Length == 2
                    && m.GetParameters()[1].ParameterType == typeof(Action<HttpClient>)
                );

            var genericMethod = method.MakeGenericMethod(clientType);
            genericMethod.Invoke(null, new object[] {
        services,
        (Action<HttpClient>)(client => { client.BaseAddress = apiBaseAddress; })
    });
        }
    }
}
