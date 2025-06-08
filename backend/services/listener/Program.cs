using listener;
using listener.Workflows;
using Temporalio.Extensions.Hosting;

var builder = Host.CreateApplicationBuilder(args);

// Настройка Temporal клиента
string temporalHost = "141.105.71.119:7233";
builder.Services.AddTemporalClient(temporalHost);
builder.Services.AddHostedTemporalWorker("news-feed-task-queue")
    .AddWorkflow<NewsListenerWorkflow>();

builder.Services.AddHostedService<Worker>();

var host = builder.Build();

Console.WriteLine("🎯 News Listener Service запускается...");
Console.WriteLine($"📡 Подключение к Temporal: {temporalHost}");
Console.WriteLine("🔄 Task Queue: news-feed-task-queue");
Console.WriteLine(new string('-', 50));

host.Run();
