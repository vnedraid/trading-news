import asyncio
from temporalio.client import Client
from workflows import RSSFeedMonitorWorkflow
import json
from dotenv import dotenv_values

async def main():
    client = await Client.connect("localhost:7233")
    
    # Загружаем RSS-ленты из .env
    config = dotenv_values("feeds.env")
    feeds_to_monitor = json.loads(config["RSS_FEEDS"])   # Безопасное преобразование
    
    for feed_name, feed_url in feeds_to_monitor.items():

        await client.start_workflow(
            RSSFeedMonitorWorkflow.run,
            args=[feed_name, feed_url],
            id=f"rss-monitor-{feed_url.split('//')[1].replace('/', '-')}",
            task_queue="rss-feed-task-queue",
        )
        print(f"Начат мониторинг ленты: {feed_name} ({feed_url})")

if __name__ == "__main__":
    asyncio.run(main())