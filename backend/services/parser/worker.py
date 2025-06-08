import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from activities import check_feed_for_updates, process_rss_item
from workflows import RSSFeedMonitorWorkflow

async def main():
    # Подключаемся к Temporal серверу
    client = await Client.connect("localhost:7233")

    # Создаем воркер
    worker = Worker(
        client,
        task_queue="rss-feed-task-queue",
        workflows=[RSSFeedMonitorWorkflow],
        activities=[check_feed_for_updates, process_rss_item],
    )
    
    print("Запуск воркера для обработки RSS-лент...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())