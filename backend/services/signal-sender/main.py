import asyncio
import json
from temporalio.client import Client
from data_generator import RSSDataGenerator


async def main():
    """Основная функция для отправки сигналов в Temporal"""
    
    # Подключаемся к локальному Temporal серверу
    client = await Client.connect("localhost:7233")
    
    print("🚀 Signal Sender запущен. Отправка сигналов каждую секунду...")
    print("📡 Подключение к Temporal: localhost:7233")
    print("📰 Генерация случайных RSS feed записей...")
    print("-" * 50)
    
    counter = 1
    
    try:
        while True:
            # Генерируем случайную RSS запись
            rss_record = RSSDataGenerator.generate_random_record()
            
            # Преобразуем в JSON для отправки
            signal_data = {
                "id": counter,
                "timestamp": rss_record.published_date.isoformat(),
                "data": rss_record.to_dict()
            }
            
            # Отправляем сигнал в workflow
            try:
                await client.get_workflow_handle("news-feed-workflow").signal(
                    "news-feed-signal",
                    signal_data
                )
                
                print(f"✅ Сигнал #{counter} отправлен:")
                print(f"   📰 {rss_record.title}")
                print(f"   🏷️  {rss_record.category} | {rss_record.sentiment}")
                print(f"   🔗 {rss_record.source}")
                print()
                
            except Exception as e:
                print(f"❌ Ошибка отправки сигнала #{counter}: {e}")
            
            counter += 1
            
            # Ждем 1 секунду перед следующим сигналом
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Остановка Signal Sender...")
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(main())
