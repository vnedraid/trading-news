using System.Text.Json.Serialization;

namespace listener.Models;

public class NewsAnalysisResponse
{
    [JsonPropertyName("tickers")]
    public List<string> Tickers { get; set; } = new();

    [JsonPropertyName("sector")]
    public string Sector { get; set; } = string.Empty;

    [JsonPropertyName("industry")]
    public string Industry { get; set; } = string.Empty;

    [JsonPropertyName("sentiment")]
    public string Sentiment { get; set; } = string.Empty;

    [JsonPropertyName("entities")]
    public List<string> Entities { get; set; } = new();

    [JsonPropertyName("summary")]
    public string Summary { get; set; } = string.Empty;

    [JsonPropertyName("confidence")]
    public double Confidence { get; set; }
}

public class NewsAnalysisTemplate
{
    [JsonPropertyName("system_prompt")]
    public string SystemPrompt { get; set; } = string.Empty;

    [JsonPropertyName("user_prompt_template")]
    public string UserPromptTemplate { get; set; } = string.Empty;

    [JsonPropertyName("response_format")]
    public ResponseFormat ResponseFormat { get; set; } = new();
}

public class ResponseFormat
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;
}

public class AnalyzedNewsRecord
{
    public string Id { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string Link { get; set; } = string.Empty;
    public DateTime PublishedAt { get; set; }
    public string Source { get; set; } = string.Empty;
    public string Category { get; set; } = string.Empty;
    public string OriginalSentiment { get; set; } = string.Empty;
    public string AnalyzedSentiment { get; set; } = string.Empty;
    public string Sector { get; set; } = string.Empty;
    public string Industry { get; set; } = string.Empty;
    public string Tickers { get; set; } = string.Empty; // JSON array as string
    public string Entities { get; set; } = string.Empty; // JSON array as string
    public string Summary { get; set; } = string.Empty;
    public double Confidence { get; set; }
    public DateTime AnalyzedAt { get; set; }
}