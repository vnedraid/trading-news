# Trading News Signal System

Система для обработки сигналов торговых новостей на базе Temporal.

## Описание

Эта система состоит из двух компонентов:
- **Signal Sender** (Python) - генерирует и отправляет сигналы с RSS feed записями каждую секунду
- **Listener** (C#) - принимает сигналы через Temporal workflow и выводит их в консоль

## Быстрый старт

### Предварительные требования

1. **Temporal Server** (должен быть запущен локально)
2. **Python 3.8+** с установленным `uv`
3. **.NET 9 SDK**

### Запуск Temporal Server

```bash
temporal server start-dev
```

### Запуск системы

```bash
./start-system.sh
```

Или запуск компонентов по отдельности:

```bash
# Терминал 1: Запуск Listener
cd backend/services/listener
dotnet run

# Терминал 2: Запуск Signal Sender
cd backend/services/signal-sender
uv run main.py
```

## Мониторинг

- **Temporal Web UI**: http://localhost:8233
- **Логи**: отображаются в консоли каждого компонента

## Структура проекта

```
trading-news/
├── backend/services/
│   ├── listener/          # C# Temporal Worker
│   ├── signal-sender/     # Python Signal Sender
│   └── README.md         # Подробная документация
├── start-system.sh       # Скрипт запуска системы
└── README.md            # Этот файл
```

## Как это работает

1. **Signal Sender** генерирует случайные RSS feed записи торговых новостей
2. Отправляет их как сигналы в Temporal workflow каждую секунду
3. **Listener** запускает Temporal workflow, который принимает сигналы
4. Полученные сигналы выводятся в консоль с детальной информацией

## Пример вывода

```
📰 Получен сигнал #1:
   📈 Центральный банк повысил ключевую ставку на 0.25%
   🏷️  Центральные банки | Reuters
   🕒 2025-06-08T10:30:00
   🔗 https://example.com/news/1234
   📝 Решение принято на фоне растущих инфляционных давлений...
   📊 Всего получено сигналов: 1
```