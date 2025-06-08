#!/bin/bash

echo "🚀 Запуск Trading News Signal System"
echo "======================================"

# Проверяем, что Temporal Server запущен
echo "📡 Проверка подключения к Temporal Server..."
if ! curl -s http://localhost:8233 > /dev/null; then
    echo "❌ Temporal Server не запущен!"
    echo "   Запустите его командой: temporal server start-dev"
    exit 1
fi

echo "✅ Temporal Server доступен"
echo ""

# Запускаем C# Listener в фоне
echo "🎯 Запуск C# Listener..."
cd backend/services/listener
dotnet run &
LISTENER_PID=$!
cd ../../..

echo "✅ Listener запущен (PID: $LISTENER_PID)"
echo ""

# Ждем немного, чтобы listener успел запуститься
sleep 3

# Запускаем Python Signal Sender
echo "📡 Запуск Python Signal Sender..."
cd backend/services/signal-sender
uv run main.py &
SENDER_PID=$!
cd ../../..

echo "✅ Signal Sender запущен (PID: $SENDER_PID)"
echo ""
echo "🎉 Система запущена!"
echo "📊 Мониторинг:"
echo "   - Temporal Web UI: http://localhost:8233"
echo "   - Логи отображаются в консоли"
echo ""
echo "⏹️  Для остановки нажмите Ctrl+C"

# Функция для корректного завершения процессов
cleanup() {
    echo ""
    echo "🛑 Остановка системы..."
    kill $LISTENER_PID 2>/dev/null
    kill $SENDER_PID 2>/dev/null
    echo "✅ Система остановлена"
    exit 0
}

# Обработка сигнала завершения
trap cleanup SIGINT SIGTERM

# Ждем завершения
wait