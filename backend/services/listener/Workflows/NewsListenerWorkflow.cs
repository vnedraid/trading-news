using Temporalio.Workflows;
using listener.Models;
using System.Text.Json;

namespace listener.Workflows;

[Workflow("news-feed-workflow")]
public class NewsListenerWorkflow
{
    private readonly List<SignalData> _receivedSignals = new();

    public NewsListenerWorkflow()
    {
    }

    [WorkflowRun]
    public async Task RunAsync()
    {
        Workflow.Logger.LogInformation("🎯 News Listener Workflow запущен и ожидает сигналы...");
        
        // Workflow будет работать бесконечно, ожидая сигналы
        await Workflow.WaitConditionAsync(() => false);
    }

    [WorkflowSignal("news-feed-signal")]
    public async Task HandleNewsSignal(SignalData signalData)
    {
        _receivedSignals.Add(signalData);
        
        var emoji = GetSentimentEmoji(signalData.Data.Sentiment);
        
        Workflow.Logger.LogInformation("📰 Получен сигнал #{Id}:", signalData.Id);
        Workflow.Logger.LogInformation("   {Emoji} {Title}", emoji, signalData.Data.Title);
        Workflow.Logger.LogInformation("   🏷️  {Category} | {Source}",
            signalData.Data.Category ?? "Без категории",
            signalData.Data.Source);
        Workflow.Logger.LogInformation("   🕒 {Timestamp}", signalData.Timestamp);
        Workflow.Logger.LogInformation("   🔗 {Link}", signalData.Data.Link);
        Workflow.Logger.LogInformation("   📝 {Description}",
            signalData.Data.Description.Length > 100
                ? signalData.Data.Description[..100] + "..."
                : signalData.Data.Description);
        Workflow.Logger.LogInformation("   📊 Всего получено сигналов: {Count}", _receivedSignals.Count);
        Workflow.Logger.LogInformation(new string('-', 80));

        

        await Task.CompletedTask;
    }

    private static string GetSentimentEmoji(string? sentiment)
    {
        return sentiment?.ToLower() switch
        {
            "positive" => "📈",
            "negative" => "📉",
            "neutral" => "➡️",
            _ => "❓"
        };
    }

    [WorkflowQuery("get_signals_count")]
    public int GetSignalsCount() => _receivedSignals.Count;

    [WorkflowQuery("get_latest_signals")]
    public List<SignalData> GetLatestSignals(int count = 10) 
        => _receivedSignals.TakeLast(count).ToList();
}