import feedparser
from datetime import datetime
from temporalio import activity
from workflows import RSSItem
from temporalio.service import RPCError
from temporalio.client import WorkflowExecutionStatus
import requests  # для более гибких запросов
import pytz  # Для работы с часовыми поясами
from temporalio.client import Client

@activity.defn
async def check_feed_for_updates(feed_url: str, last_processed_guid: str = None) -> list:
    """Проверяет RSS-ленту с обработкой 406 и других ошибок"""
    try:
        # Попробуем через requests (более гибко)
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Referer": "https://www.forexfactory.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })

        try:
            response = session.get(feed_url, timeout=10)
            response.raise_for_status()
            feed_content = response.content
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 406:
                raise ValueError("Сервер отверг запрос. Попробуйте другой User-Agent или URL.")
            raise ValueError(f"HTTP ошибка {e.response.status_code}: {str(e)}")

        feed = feedparser.parse(feed_content)

        # Обработка записей
        new_items = []
        is_new = True
        file = open("file.csv", "w")
        for entry in feed.entries:
            if is_new:
                for key in entry.keys():
                    file.write(f"{key}, ")
                file.write("\n")
                is_new = False
            try:
                guid = entry.get('id') or entry.get('guid') or entry.get('link', '')
                if last_processed_guid and guid == last_processed_guid:
                    break

                # Парсинг даты из published
                pub_date_str = entry.get('published', '')
                if pub_date_str:
                    try:
                        # Формат: 'Fri, 6 Jun 2025 08:49:00 +0300'
                        pub_date = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %z')
                    except ValueError:
                        # Альтернативный формат, если основной не подходит
                        pub_date = datetime.now(pytz.UTC)
                else:
                    pub_date = datetime.now(pytz.UTC)
                for key in entry.keys():
                    file.write(f"{entry[key]}, ")
                file.write("\n")
                new_items.append(RSSItem(
                    feed_url=feed_url,
                    title=entry.get('title', 'Без названия'),
                    link=entry.get('link', ''),
                    description=entry.get('description', ''),
                    published_at=pub_date,
                    guid=guid
                ).to_dict())
            except Exception as e:
                activity.logger.warning(f"Ошибка обработки записи: {str(e)}")
                continue
        file.close()

        return new_items[::-1] if new_items else []

    except Exception as e:
        activity.logger.error(f"Ошибка при обработке {feed_url}: {str(e)}")
        return


@activity.defn
async def process_rss_item(feed_name: str, item_data: dict) -> None:
    """Обрабатывает новую запись из RSS (отправка в очередь)"""
    item = RSSItem.from_dict(item_data)
    # Здесь логика обработки
    
    try:
        # Подключаемся к удалённому Temporal
        remote_client = await Client.connect("141.105.71.11:7233")

        # Получаем хэндл общего Workflow (ID фиксированный)
        workflow_handle = remote_client.get_workflow_handle("news-feed-workflow")

        # Проверяем статус workflow перед отправкой сигнала
        try:
            desc = await workflow_handle.describe()
            if desc.status != WorkflowExecutionStatus.RUNNING:
                activity.logger.warning(
                    f"Workflow не запущен (статус: {desc.status}). "
                    f"Элемент не будет отправлен: {item_data['guid']}"
                )
                return
        except Exception as e:
            activity.logger.error(f"Ошибка при проверке статуса workflow: {str(e)}")
            raise

        send_data = {
            "id": item.guid,
            "timestamp": datetime.now().isoformat(),
            "data": item_data
        }

        # Отправляем элемент через Signal с обработкой ошибки
        try:
            await workflow_handle.signal(
                "news-feed-signal",
                send_data,
            )
            activity.logger.info(f"📤 Успешно отправлен элемент: {item_data['guid']}")
        except RPCError as e:
            if "workflow execution already completed" in str(e):
                activity.logger.warning(
                    f"Workflow уже завершен. Элемент не отправлен: {item_data['guid']}"
                )
            else:
                raise

    except Exception as e:
        activity.logger.error(f"Ошибка при обработке элемента {item_data['guid']}: {str(e)}")
        return
