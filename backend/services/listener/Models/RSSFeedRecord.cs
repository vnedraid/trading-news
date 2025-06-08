using System.Text.Json.Serialization;

namespace listener.Models;

/*
feed_url: str  # URL RSS-ленты
title: str     # Заголовок новости
link: str      # Ссылка на новость
description: str  # Описание
published_at: datetime  # Время публикации
guid: str      # Уникальный идентификатор
*/

public class RSSFeedRecord
{
    [JsonPropertyName("title")]
    public string Title { get; set; } = string.Empty;

    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    [JsonPropertyName("link")]
    public string Link { get; set; } = string.Empty;

    [JsonPropertyName("published_at")]
    public string PublishedDate { get; set; } = string.Empty;

    [JsonPropertyName("feed_url")]
    public string Source { get; set; } = string.Empty;

    [JsonPropertyName("guid")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("category")]
    public string? Category { get; set; }

    [JsonPropertyName("sentiment")]
    public string? Sentiment { get; set; }
}

public class SignalData
{
    [JsonPropertyName("id")]
    public required string Id { get; set; }
    
    [JsonPropertyName("timestamp")]
    public string Timestamp { get; set; } = string.Empty;
    
    [JsonPropertyName("data")]
    public RSSFeedRecord Data { get; set; } = new();
}