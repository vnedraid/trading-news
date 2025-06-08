using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using listener.Models;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

namespace listener.Services;

public interface ILLMService
{
    Task<NewsAnalysisResponse?> AnalyzeNewsAsync(RSSFeedRecord newsRecord);
}

public class LLMService : ILLMService
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<LLMService> _logger;
    private readonly string _apiKey;
    private readonly string _baseUrl;
    private readonly string _model;
    private string _systemPrompt = string.Empty;
    private string _userPromptTemplate = string.Empty;

    public LLMService(HttpClient httpClient, IConfiguration configuration, ILogger<LLMService> logger)
    {
        _httpClient = httpClient;
        _logger = logger;
        _apiKey = configuration["OpenRouter:ApiKey"] ?? throw new ArgumentException("OpenRouter API key not found");
        _baseUrl = configuration["OpenRouter:BaseUrl"] ?? throw new ArgumentException("OpenRouter base URL not found");
        _model = configuration["OpenRouter:Model"] ?? throw new ArgumentException("OpenRouter model not found");
        
        // Load prompts from markdown file
        LoadPromptsFromMarkdown();
        
        // Configure HttpClient
        _httpClient.DefaultRequestHeaders.Add("Authorization", $"Bearer {_apiKey}");
        _httpClient.DefaultRequestHeaders.Add("HTTP-Referer", "https://trading-news-app.com");
        _httpClient.DefaultRequestHeaders.Add("X-Title", "Trading News Analyzer");
    }

    private void LoadPromptsFromMarkdown()
    {
        try
        {
            var promptPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Templates", "news-analysis-prompt.md");
            var promptContent = File.ReadAllText(promptPath);
            
            // Extract system prompt (content between "## System Prompt" and "## User Prompt Template")
            var systemPromptStart = promptContent.IndexOf("## System Prompt") + "## System Prompt".Length;
            var systemPromptEnd = promptContent.IndexOf("## User Prompt Template");
            _systemPrompt = promptContent.Substring(systemPromptStart, systemPromptEnd - systemPromptStart).Trim();
            
            // Extract user prompt template (content between "## User Prompt Template" and "## IMPORTANT CONSTRAINTS")
            var userPromptStart = promptContent.IndexOf("## User Prompt Template") + "## User Prompt Template".Length;
            var userPromptEnd = promptContent.IndexOf("## Response Format");
            var userPromptSection = promptContent.Substring(userPromptStart, userPromptEnd - userPromptStart).Trim();
            
            // Build the complete user prompt template
            _userPromptTemplate = userPromptSection;
            
            _logger.LogInformation("✅ Successfully loaded prompts from markdown file");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to load prompts from markdown file");
            throw;
        }
    }

    public async Task<NewsAnalysisResponse?> AnalyzeNewsAsync(RSSFeedRecord newsRecord)
    {
        try
        {
            var userPrompt = _userPromptTemplate
                .Replace("{title}", newsRecord.Title)
                .Replace("{description}", newsRecord.Description)
                .Replace("{source}", newsRecord.Source)
                .Replace("{published_at}", newsRecord.PublishedDate);

            var requestBody = new
            {
                model = _model,
                messages = new[]
                {
                    new { role = "system", content = _systemPrompt },
                    new { role = "user", content = userPrompt }
                },
                response_format = new { type = "json_object" },
                temperature = 0.1,
                max_tokens = 1000
            };

            var json = JsonSerializer.Serialize(requestBody);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            _logger.LogInformation("🤖 Sending news to LLM for analysis: {Title}", newsRecord.Title);

            var response = await _httpClient.PostAsync($"{_baseUrl}/chat/completions", content);
            
            if (!response.IsSuccessStatusCode)
            {
                var errorContent = await response.Content.ReadAsStringAsync();
                _logger.LogError("LLM API request failed: {StatusCode} - {Content}", response.StatusCode, errorContent);
                return null;
            }

            var responseContent = await response.Content.ReadAsStringAsync();
            var llmResponse = JsonSerializer.Deserialize<LLMResponse>(responseContent);

            if (llmResponse?.Choices?.FirstOrDefault()?.Message?.Content == null)
            {
                _logger.LogWarning("LLM response is empty or invalid");
                return null;
            }

            var analysisJson = llmResponse.Choices.First().Message.Content;
            var analysis = JsonSerializer.Deserialize<NewsAnalysisResponse>(analysisJson);

            _logger.LogInformation("✅ LLM analysis completed for: {Title}", newsRecord.Title);
            _logger.LogInformation("   📊 Sector: {Sector}, Sentiment: {Sentiment}, Confidence: {Confidence:P1}", 
                analysis?.Sector, analysis?.Sentiment, analysis?.Confidence);

            return analysis;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error analyzing news with LLM: {Title}", newsRecord.Title);
            return null;
        }
    }
}

// Helper classes for LLM API response
public class LLMResponse
{
    [JsonPropertyName("choices")]
    public List<Choice> Choices { get; set; } = new();
}

public class Choice
{
    [JsonPropertyName("message")]
    public Message Message { get; set; } = new();
}

public class Message
{
    [JsonPropertyName("content")]
    public string Content { get; set; } = string.Empty;
}