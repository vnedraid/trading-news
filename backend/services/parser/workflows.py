from temporalio import workflow
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

@dataclass
class RSSItem:
    feed_url: str  # URL RSS-ленты
    title: str     # Заголовок новости
    link: str      # Ссылка на новость
    description: str  # Описание
    published_at: datetime  # Время публикации
    guid: str      # Уникальный идентификатор

    # метод для сериализации
    def to_dict(self):
        return {
            'feed_url': self.feed_url,
            'title': self.title,
            'link': self.link,
            'description': self.description,
            'published_at': self.published_at.isoformat(),  # Конвертируем datetime в строку
            'guid': self.guid
        }

    # метод для десериализации
    @classmethod
    def from_dict(cls, data):
        return cls(
            feed_url=data['feed_url'],
            title=data['title'],
            link=data['link'],
            description=data['description'],
            published_at=datetime.fromisoformat(data['published_at']),  # Конвертируем строку обратно в datetime
            guid=data['guid']
        )

@workflow.defn
class RSSFeedMonitorWorkflow:
    def __init__(self) -> None:
        self._last_processed_guid: Optional[str] = None

    @workflow.run
    async def run(self, feed_name: str, feed_url: str, check_interval_seconds: int = 300) -> None:
        while True:
            new_items_data = await workflow.execute_activity(
                "check_feed_for_updates",
                args=[feed_url, self._last_processed_guid],
                start_to_close_timeout=timedelta(seconds=30),
            )

            if new_items_data:
                # Первый элемент уже будет словарем
                self._last_processed_guid = new_items_data[0]['guid']
                
                for item_data in new_items_data:
                    await workflow.execute_activity(
                        "process_rss_item",
                        args=[feed_name, item_data],  # Передаем словарь
                        start_to_close_timeout=timedelta(seconds=30),
                    )

            await workflow.sleep(check_interval_seconds)