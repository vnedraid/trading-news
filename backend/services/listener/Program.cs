using listener;
using listener.Workflows;
using listener.Services;
using Temporalio.Extensions.Hosting;

var builder = Host.CreateApplicationBuilder(args);

// Add configuration sources
builder.Configuration.AddJsonFile("appsettings.secrets.json", optional: true, reloadOnChange: true);

// Настройка Temporal клиента
string temporalHost = "localhost:7233";
builder.Services.AddTemporalClient(temporalHost);
builder.Services.AddHostedTemporalWorker("news-feed-task-queue")
    .AddWorkflow<NewsListenerWorkflow>();

// Register services
builder.Services.AddHttpClient<ILLMService, LLMService>();
builder.Services.AddScoped<IPostgreSQLService, PostgreSQLService>();
builder.Services.AddScoped<listener.Activities.NewsAnalysisActivity>();

builder.Services.AddHostedService<Worker>();
builder.Services.AddHostedService<NewsAnalysisBackgroundService>();

var host = builder.Build();

// Initialize database
using (var scope = host.Services.CreateScope())
{
    var dbService = scope.ServiceProvider.GetRequiredService<IPostgreSQLService>();
    await dbService.InitializeDatabaseAsync();
}

Console.WriteLine("🎯 News Listener Service запускается...");
Console.WriteLine($"📡 Подключение к Temporal: {temporalHost}");
Console.WriteLine("🔄 Task Queue: news-feed-task-queue");
Console.WriteLine("🗄️ PostgreSQL: Initialized");
Console.WriteLine("🤖 LLM Service: Ready");
Console.WriteLine(new string('-', 50));

host.Run();
