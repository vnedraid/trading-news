using Temporalio.Client;
using listener.Workflows;

namespace listener;

public class Worker : BackgroundService
{
    private readonly ILogger<Worker> _logger;
    private readonly ITemporalClient _temporalClient;

    public Worker(ILogger<Worker> logger, ITemporalClient temporalClient)
    {
        _logger = logger;
        _temporalClient = temporalClient;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        const string workflowId = "news-feed-workflow";
        WorkflowHandle<NewsListenerWorkflow>? workflowHandle = null;
        
        try
        {
            _logger.LogInformation("🚀 Запуск News Listener Workflow...");
            
            try
            {
                // Пытаемся запустить новый workflow
                workflowHandle = await _temporalClient.StartWorkflowAsync(
                    (NewsListenerWorkflow wf) => wf.RunAsync(),
                    new WorkflowOptions
                    {
                        Id = workflowId,
                        TaskQueue = "news-feed-task-queue"
                    });
                
                _logger.LogInformation("✅ Новый workflow запущен с ID: {WorkflowId}", workflowHandle.Id);
            }
            catch (Temporalio.Exceptions.WorkflowAlreadyStartedException)
            {
                // Если workflow уже существует, проверяем его статус
                _logger.LogInformation("🔄 Workflow уже существует, проверяем статус...");
                workflowHandle = _temporalClient.GetWorkflowHandle<NewsListenerWorkflow>(workflowId);
                
                try
                {
                    // Проверяем, активен ли workflow
                    var description = await workflowHandle.DescribeAsync();
                    
                    if (description.Status == Temporalio.Api.Enums.V1.WorkflowExecutionStatus.Canceled ||
                        description.Status == Temporalio.Api.Enums.V1.WorkflowExecutionStatus.Terminated ||
                        description.Status == Temporalio.Api.Enums.V1.WorkflowExecutionStatus.Failed ||
                        description.Status == Temporalio.Api.Enums.V1.WorkflowExecutionStatus.Completed)
                    {
                        _logger.LogInformation("🔄 Старый workflow завершен ({Status}), создаем новый...", description.Status);
                        
                        // Создаем новый workflow с уникальным ID
                        var newWorkflowId = $"{workflowId}-{DateTime.UtcNow:yyyyMMdd-HHmmss}";
                        workflowHandle = await _temporalClient.StartWorkflowAsync(
                            (NewsListenerWorkflow wf) => wf.RunAsync(),
                            new WorkflowOptions
                            {
                                Id = newWorkflowId,
                                TaskQueue = "news-feed-task-queue"
                            });
                        
                        _logger.LogInformation("✅ Новый workflow запущен с ID: {WorkflowId}", workflowHandle.Id);
                    }
                    else
                    {
                        _logger.LogInformation("✅ Подключились к активному workflow с ID: {WorkflowId}", workflowHandle.Id);
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogWarning(ex, "⚠️ Не удалось проверить статус workflow, создаем новый...");
                    
                    // Создаем новый workflow с уникальным ID
                    var newWorkflowId = $"{workflowId}-{DateTime.UtcNow:yyyyMMdd-HHmmss}";
                    workflowHandle = await _temporalClient.StartWorkflowAsync(
                        (NewsListenerWorkflow wf) => wf.RunAsync(),
                        new WorkflowOptions
                        {
                            Id = newWorkflowId,
                            TaskQueue = "news-feed-task-queue"
                        });
                    
                    _logger.LogInformation("✅ Новый workflow запущен с ID: {WorkflowId}", workflowHandle.Id);
                }
            }

            _logger.LogInformation("🎧 Ожидание сигналов от Signal Sender...");
            _logger.LogInformation("💡 Нажмите Ctrl+C для остановки сервиса и workflow");
            
            // Ждем либо завершения workflow, либо сигнала остановки
            var workflowTask = workflowHandle.GetResultAsync();
            var cancellationTask = Task.Delay(Timeout.Infinite, stoppingToken);
            
            await Task.WhenAny(workflowTask, cancellationTask);
            
            if (stoppingToken.IsCancellationRequested)
            {
                _logger.LogInformation("🛑 Получен сигнал остановки, завершаем работу...");
                await StopWorkflowAsync(workflowHandle);
                return;
            }
            
            // Если workflow завершился сам по себе
            await workflowTask;
        }
        catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
        {
            _logger.LogInformation("🛑 Сервис остановлен пользователем");
            if (workflowHandle != null)
            {
                await StopWorkflowAsync(workflowHandle);
            }
        }
        catch (Temporalio.Exceptions.WorkflowFailedException ex) when (ex.InnerException is Temporalio.Exceptions.CanceledFailureException)
        {
            _logger.LogInformation("🔄 Workflow был отменен, это нормально при остановке сервиса");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "💥 Ошибка при запуске workflow");
            throw;
        }
    }

    private async Task StopWorkflowAsync(WorkflowHandle<NewsListenerWorkflow> workflowHandle)
    {
        try
        {
            _logger.LogInformation("🔄 Останавливаем workflow {WorkflowId}...", workflowHandle.Id);
            
            // Получаем количество обработанных сигналов перед остановкой
            var signalsCount = await workflowHandle.QueryAsync(wf => wf.GetSignalsCount());
            _logger.LogInformation("📊 Workflow обработал {Count} сигналов", signalsCount);
            
            // Отменяем workflow
            await workflowHandle.CancelAsync();
            _logger.LogInformation("✅ Workflow успешно остановлен");
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "⚠️ Не удалось корректно остановить workflow, возможно он уже завершен");
        }
    }
}
