#!/bin/bash

# Start server in background
echo "Starting server..."
bun run index.ts &
SERVER_PID=$!

# Wait for server to start
sleep 2

# Run tests
echo "Running download-status tests..."
bun test tests/download-status.test.ts

# Kill server
kill $SERVER_PID

echo "Done!"
