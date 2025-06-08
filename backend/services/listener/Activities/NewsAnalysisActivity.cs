using System.Text.Json;
using listener.Models;
using listener.Services;
using Microsoft.Extensions.Logging;
using Temporalio.Activities;

namespace listener.Activities;

public class NewsAnalysisActivity
{
    private readonly ILLMService _llmService;
    private readonly IPostgreSQLService _dbService;
    private readonly ILogger<NewsAnalysisActivity> _logger;

    public NewsAnalysisActivity(
        ILLMService llmService, 
        IPostgreSQLService dbService, 
        ILogger<NewsAnalysisActivity> logger)
    {
        _llmService = llmService;
        _dbService = dbService;
        _logger = logger;
    }

    [Activity("analyze-and-save-news")]
    public async Task AnalyzeAndSaveNewsAsync(SignalData signalData)
    {
        try
        {
            _logger.LogInformation("🔍 Starting analysis for news: {Title}", signalData.Data.Title);

            // Step 1: Analyze news with LLM
            var analysisResult = await _llmService.AnalyzeNewsAsync(signalData.Data);
            
            if (analysisResult == null)
            {
                _logger.LogWarning("⚠️ LLM analysis returned null for news: {Title}", signalData.Data.Title);
                return;
            }

            // Step 2: Convert to database record
            var analyzedRecord = ConvertToAnalyzedNewsRecord(signalData, analysisResult);

            // Step 3: Save to database
            await _dbService.SaveAnalyzedNewsAsync(analyzedRecord);

            _logger.LogInformation("✅ Successfully analyzed and saved news: {Title}", signalData.Data.Title);
            _logger.LogInformation("   📊 Analysis: Sector={Sector}, Sentiment={Sentiment}, Confidence={Confidence:P1}", 
                analysisResult.Sector, analysisResult.Sentiment, analysisResult.Confidence);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "❌ Failed to analyze and save news: {Title}", signalData.Data.Title);
            throw;
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