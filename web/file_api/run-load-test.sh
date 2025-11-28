#!/bin/bash

# Запускаємо сервер у фоновому режимі
echo "Starting server..."
bun run index.ts &
SERVER_PID=$!

# Чекаємо поки сервер запуститься
sleep 3

# Перевіряємо чи сервер запущений
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "Error: Server failed to start"
    exit 1
fi

echo "Server started with PID: $SERVER_PID"
echo "Running load tests..."

# Запускаємо тести
bun test ./tests/get-creds-load.test.ts

TEST_EXIT_CODE=$?

# Зупиняємо сервер
echo "Stopping server..."
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null

exit $TEST_EXIT_CODE
