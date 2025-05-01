using System.Threading.Tasks;

using Microsoft.EntityFrameworkCore;

namespace Recommendation_System.Auth.Services;

    public interface IGeneralSettingsService
    {
        Task<string> GetValueAsync(string key);
    }

    public class GeneralSettingsService : IGeneralSettingsService
    {
        private readonly AuthDbContext _context;

        public GeneralSettingsService(AuthDbContext context)
        {
            _context = context;
        }

        public async Task<string> GetValueAsync(string key)
        {
            var setting = await _context.GeneralSettings.FirstOrDefaultAsync(s => s.Key == key);
            if (setting == null)
            {
                throw new InvalidOperationException($"Setting with key '{key}' not found.");
            }

            return setting.Value;
        }
    }

