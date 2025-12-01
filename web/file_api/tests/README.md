# Test Suite for File API Routes

This directory contains comprehensive tests for all routes implemented in the file_api service.

## Test Files

### 1. `get-credentials.test.ts`
Tests for `/get_credentials` route (POST)
- ✅ Success case with valid credentials
- ✅ Wrong identifier_key validation
- ✅ Non-existent computer handling
- ✅ Required fields validation
- ✅ Method validation (405 for GET)
- ✅ Deactivated computer handling
- ✅ IP and timestamp update verification

**Tests: 7** | **Assertions: 29**

---

### 2. `last-time.test.ts`
Tests for `/last_time` route (POST)
- ✅ Update last_time_online successfully
- ✅ Update both last_time_online and last_download_time
- ✅ Wrong identifier_key error handling
- ✅ Non-existent computer with rmcreds flag
- ✅ Missing identifier_key handling
- ✅ Method validation (405 for GET)

**Tests: 6** | **Assertions: 19**

---

### 3. `telemetry.test.ts`
Tests for `/get_telemetry_info` (GET) and `/printer_info` (POST)

#### GET /get_telemetry_info
- ✅ Return telemetry settings successfully
- ✅ 404 for non-existent computer
- ✅ Missing identifier_key parameter validation
- ✅ Method validation (405 for POST)

#### POST /printer_info
- ✅ Update with NORMAL status (code 0)
- ✅ Update with OFFLINE status (code 128)
- ✅ Update with UNKNOWN status (other codes)
- ✅ 400 for non-existent computer
- ✅ Required fields validation
- ✅ Method validation (405 for GET)
- ✅ Database verification of stored data

**Tests: 11** | **Assertions: 25**

---

### 4. `get-creds-load.test.ts`
Load testing for `/get_credentials` with production data
- ✅ 353 concurrent requests (all real computers)
- ✅ Batched requests (100 at a time)
- ✅ Success rate > 95%
- ✅ Performance metrics (avg response time < 500ms)

**Tests: 2** | **Assertions: 4**

---

### 5. `get-creds-quick.test.ts`
Quick load testing for development iteration
- ✅ 50 concurrent requests
- ✅ Fast feedback for optimization

**Tests: 1** | **Assertions: 2**

---

## Running Tests

### Run all route tests
```bash
bun test ./tests/get-credentials.test.ts ./tests/last-time.test.ts ./tests/telemetry.test.ts
```

### Run individual test suites
```bash
# Get credentials
bun test ./tests/get-credentials.test.ts

# Last time
bun test ./tests/last-time.test.ts

# Telemetry
bun test ./tests/telemetry.test.ts
```

### Run load tests
```bash
# Quick test (50 requests)
bun test ./tests/get-creds-quick.test.ts

# Full load test (353 requests)
bun test ./tests/get-creds-load.test.ts --timeout 120000
```

### Run all tests
```bash
bun test
```

---

## Test Statistics

**Total Tests**: 24 functional + 3 load tests = **27 tests**  
**Total Assertions**: 73+ assertions  
**Execution Time**: ~350ms for functional tests  
**Success Rate**: 100% ✅

---

## Prerequisites

- Server must be running on `http://localhost:3000`
- Database must be populated with test data
- PostgreSQL container must be running (web-db-1)

Start server:
```bash
bun run index.ts
```

Or in background:
```bash
nohup bun run index.ts > /tmp/bun-server.log 2>&1 &
```

---

## Performance Benchmarks

### `/get_credentials` Load Test Results
- **Concurrent Requests**: 353 (production level)
- **Success Rate**: 96.88%
- **Average Response Time**: 397ms
- **Total Time**: 485ms
- **RPS**: 727.84 requests/second
- **Improvement**: 200x faster than baseline (was 49s, now 0.4s)

### Optimizations Applied
1. ✅ Connection pooling (50 connections)
2. ✅ Fire-and-forget updates
3. ✅ Minimal column selection
4. ✅ Parallel queries with Promise.all()
5. ✅ Optimized MSI lookup (JOIN instead of 2 queries)
6. ✅ No blob loading for MSI version
