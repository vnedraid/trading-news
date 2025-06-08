using System.Collections.Concurrent;
using System.Text.Json;
using listener.Models;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Temporalio.Client;

namespace listener.Services;

public class NewsAnalysisBackgroundService : BackgroundService
{
    private readonly ILogger<NewsAnalysisBackgroundService> _logger;
    private readonly IServiceProvider _serviceProvider;
    private readonly ITemporalClient _temporalClient;
    private readonly ConcurrentQueue<SignalData> _newsQueue = new();

    public NewsAnalysisBackgroundService(
        ILogger<NewsAnalysisBackgroundService> logger,
        IServiceProvider serviceProvider,
        ITemporalClient temporalClient)
    {
        _logger = logger;
        _serviceProvider = serviceProvider;
        _temporalClient = temporalClient;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _logger.LogInformation("🤖 News Analysis Background Service started");

        // Process news from the queue
        await ProcessNewsQueue(stoppingToken);
    }

    private async Task ProcessNewsQueue(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                // Check for news in the queue
                if (listener.Workflows.NewsListenerWorkflow.TryDequeueNews(out var newsData) && newsData != null)
                {
                    await ProcessNewsSignal(newsData, stoppingToken);
                }
                else
                {
                    // No news to process, wait a bit
                    await Task.Delay(TimeSpan.FromSeconds(2), stoppingToken);
                }
            }
            catch (Exception ex) when (!stoppingToken.IsCancellationRequested)
            {
                _logger.LogError(ex, "Error processing news queue");
                await Task.Delay(TimeSpan.FromSeconds(5), stoppingToken);
            }
        }
    }

    private async Task ProcessNewsSignal(SignalData signalData, CancellationToken stoppingToken)
    {
        try
        {
            using var scope = _serviceProvider.CreateScope();
            var llmService = scope.ServiceProvider.GetRequiredService<ILLMService>();
            var dbService = scope.ServiceProvider.GetRequiredService<IPostgreSQLService>();

            _logger.LogInformation("🔍 Starting LLM analysis for: {Title}", signalData.Data.Title);

            // Step 1: Analyze news with LLM
            var analysisResult = await llmService.AnalyzeNewsAsync(signalData.Data);
            
            if (analysisResult == null)
            {
                _logger.LogWarning("⚠️ LLM analysis returned null for news: {Title}", signalData.Data.Title);
                return;
            }

            // Step 2: Convert to database record
            var analyzedRecord = ConvertToAnalyzedNewsRecord(signalData, analysisResult);

            // Step 3: Save to database
            await dbService.SaveAnalyzedNewsAsync(analyzedRecord);

            _logger.LogInformation("✅ Successfully analyzed and saved news: {Title}", signalData.Data.Title);
            _logger.LogInformation("   📊 Analysis: Sector={Sector}, Sentiment={Sentiment}, Confidence={Confidence:P1}", 
                analysisResult.Sector, analysisResult.Sentiment, analysisResult.Confidence);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "❌ Failed to analyze and save news: {Title}", signalData.Data.Title);
        }
    }

    private static AnalyzedNewsRecord ConvertToAnalyzedNewsRecord(SignalData signalData, NewsAnalysisResponse analysis)
    {
        // Parse published date
        DateTime publishedAt = DateTime.UtcNow;
        if (!string.IsNullOrEmpty(signalData.Data.PublishedDate))
        {
            if (!DateTime.TryParse(signalData.Data.PublishedDate, out publishedAt))
            {
                publishedAt = DateTime.UtcNow;
            }
        }

        return new AnalyzedNewsRecord
        {
            Id = signalData.Data.Id,
            Title = signalData.Data.Title,
            Description = signalData.Data.Description,
            Link = signalData.Data.Link,
            PublishedAt = publishedAt,
            Source = signalData.Data.Source,
            Category = signalData.Data.Category ?? string.Empty,
            OriginalSentiment = signalData.Data.Sentiment ?? string.Empty,
            AnalyzedSentiment = analysis.Sentiment,
            Sector = analysis.Sector,
            Industry = analysis.Industry,
            Tickers = JsonSerializer.Serialize(analysis.Tickers),
            Entities = JsonSerializer.Serialize(analysis.Entities),
            Summary = analysis.Summary,
            Confidence = analysis.Confidence,
            AnalyzedAt = DateTime.UtcNow
        };
    }
}