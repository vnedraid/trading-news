# Trading News Signal System

Система для обработки сигналов торговых новостей на базе Temporal.

## Компоненты

### 1. Signal Sender (Python)
- **Путь**: `signal-sender/`
- **Описание**: Отправляет сигналы с RSS feed записями каждую секунду
- **Технологии**: Python, Temporal SDK

### 2. Listener (C#)
- **Путь**: `listener/`
- **Описание**: Принимает сигналы и выводит их в консоль
- **Технологии**: .NET 9, Temporal SDK

## Предварительные требования

1. **Temporal Server** должен быть запущен локально на порту 7233
2. **Python 3.8+** с установленным `uv`
3. **.NET 9 SDK**

## Запуск системы

### 1. Запуск Temporal Server (если еще не запущен)
```bash
temporal server start-dev
```

### 2. Запуск Listener (C#)
```bash
cd listener
dotnet run
```

### 3. Запуск Signal Sender (Python)
```bash
cd signal-sender
uv run main.py
```

## Как это работает

1. **Signal Sender** генерирует случайные RSS feed записи и отправляет их как сигналы в Temporal workflow каждую секунду
2. **Listener** запускает Temporal workflow, который принимает эти сигналы и выводит информацию в консоль
3. Все взаимодействие происходит через Temporal Server

## Структура данных

### RSS Feed Record
```json
{
  "id": 1,
  "timestamp": "2025-06-08T10:30:00",
  "data": {
    "title": "Центральный банк повысил ключевую ставку на 0.25%",
    "description": "Решение принято на фоне растущих инфляционных давлений...",
    "link": "https://example.com/news/1234",
    "published_date": "2025-06-08T10:29:45",
    "source": "Reuters",
    "category": "Центральные банки",
    "sentiment": "neutral"
  }
}
```

## Мониторинг

- Логи Signal Sender показывают отправленные сигналы
- Логи Listener показывают полученные сигналы с детальной информацией
- Temporal Web UI доступен по адресу: http://localhost:8233