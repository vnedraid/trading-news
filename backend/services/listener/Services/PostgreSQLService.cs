using System.Text.Json;
using listener.Models;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Npgsql;

namespace listener.Services;

public interface IPostgreSQLService
{
    Task InitializeDatabaseAsync();
    Task SaveAnalyzedNewsAsync(AnalyzedNewsRecord record);
}

public class PostgreSQLService : IPostgreSQLService
{
    private readonly string _connectionString;
    private readonly ILogger<PostgreSQLService> _logger;

    public PostgreSQLService(IConfiguration configuration, ILogger<PostgreSQLService> logger)
    {
        _connectionString = configuration["PostgreSQL:ConnectionString"] 
            ?? throw new ArgumentException("PostgreSQL connection string not found");
        _logger = logger;
    }

    public async Task InitializeDatabaseAsync()
    {
        try
        {
            using var connection = new NpgsqlConnection(_connectionString);
            await connection.OpenAsync();

            var createTableSql = @"
                CREATE TABLE IF NOT EXISTS analyzed_news (
                    id VARCHAR(255) PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    link TEXT,
                    published_at TIMESTAMP,
                    source VARCHAR(500),
                    category VARCHAR(100),
                    original_sentiment VARCHAR(50),
                    analyzed_sentiment VARCHAR(50),
                    sector VARCHAR(100),
                    industry VARCHAR(200),
                    tickers JSONB,
                    entities JSONB,
                    summary TEXT,
                    confidence DECIMAL(5,4),
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Add industry column if it doesn't exist (for existing tables)
                ALTER TABLE analyzed_news ADD COLUMN IF NOT EXISTS industry VARCHAR(200);

                CREATE INDEX IF NOT EXISTS idx_analyzed_news_analyzed_at ON analyzed_news(analyzed_at);
                CREATE INDEX IF NOT EXISTS idx_analyzed_news_sector ON analyzed_news(sector);
                CREATE INDEX IF NOT EXISTS idx_analyzed_news_industry ON analyzed_news(industry);
                CREATE INDEX IF NOT EXISTS idx_analyzed_news_sentiment ON analyzed_news(analyzed_sentiment);
            ";

            using var command = new NpgsqlCommand(createTableSql, connection);
            await command.ExecuteNonQueryAsync();

            _logger.LogInformation("✅ PostgreSQL table 'analyzed_news' initialized successfully");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "❌ Failed to initialize PostgreSQL table");
            throw;
        }
    }

    public async Task SaveAnalyzedNewsAsync(AnalyzedNewsRecord record)
    {
        try
        {
            using var connection = new NpgsqlConnection(_connectionString);
            await connection.OpenAsync();

            var insertSql = @"
                INSERT INTO analyzed_news (
                    id, title, description, link, published_at, source, category,
                    original_sentiment, analyzed_sentiment, sector, industry, tickers, entities,
                    summary, confidence, analyzed_at
                ) VALUES (
                    @id, @title, @description, @link, @published_at, @source, @category,
                    @original_sentiment, @analyzed_sentiment, @sector, @industry, @tickers::jsonb, @entities::jsonb,
                    @summary, @confidence, @analyzed_at
                )
                ON CONFLICT (id) DO UPDATE SET
                    analyzed_sentiment = EXCLUDED.analyzed_sentiment,
                    sector = EXCLUDED.sector,
                    industry = EXCLUDED.industry,
                    tickers = EXCLUDED.tickers,
                    entities = EXCLUDED.entities,
                    summary = EXCLUDED.summary,
                    confidence = EXCLUDED.confidence,
                    analyzed_at = EXCLUDED.analyzed_at;";

            using var command = new NpgsqlCommand(insertSql, connection);
            
            command.Parameters.AddWithValue("@id", record.Id);
            command.Parameters.AddWithValue("@title", record.Title);
            command.Parameters.AddWithValue("@description", record.Description ?? (object)DBNull.Value);
            command.Parameters.AddWithValue("@link", record.Link ?? (object)DBNull.Value);
            command.Parameters.AddWithValue("@published_at", record.PublishedAt);
            command.Parameters.AddWithValue("@source", record.Source ?? (object)DBNull.Value);
            command.Parameters.AddWithValue("@category", record.Category ?? (object)DBNull.Value);
            command.Parameters.AddWithValue("@original_sentiment", record.OriginalSentiment ?? (object)DBNull.Value);
            command.Parameters.AddWithValue("@analyzed_sentiment", record.AnalyzedSentiment ?? (object)DBNull.Value);
            command.Parameters.AddWithValue("@sector", record.Sector ?? (object)DBNull.Value);
            command.Parameters.AddWithValue("@industry", record.Industry ?? (object)DBNull.Value);
            command.Parameters.AddWithValue("@tickers", record.Tickers ?? "[]");
            command.Parameters.AddWithValue("@entities", record.Entities ?? "[]");
            command.Parameters.AddWithValue("@summary", record.Summary ?? (object)DBNull.Value);
            command.Parameters.AddWithValue("@confidence", record.Confidence);
            command.Parameters.AddWithValue("@analyzed_at", record.AnalyzedAt);

            await command.ExecuteNonQueryAsync();

            _logger.LogInformation("💾 Saved analyzed news to PostgreSQL: {Title}", record.Title);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "❌ Failed to save analyzed news to PostgreSQL: {Title}", record.Title);
            throw;
        }
    }
}