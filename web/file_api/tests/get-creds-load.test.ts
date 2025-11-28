import { describe, it, expect, beforeAll } from "bun:test";
import { drizzle } from "drizzle-orm/node-postgres";
import * as schemas from "../drizzle/schema";

const db = drizzle(process.env.DATABASE_URL!, { schema: schemas });

describe("Load Testing - getCredentials", () => {
  let computers: Array<{ identifier_key: string; computer_name: string }> = [];

  beforeAll(async () => {
    console.log("Fetching real computer data from database...");
    const allComputers = await db.query.computers.findMany({
      where: (computers, { eq }) => eq(computers.isDeleted, false),
      limit: 410,
    });

    computers = allComputers.map((c) => ({
      identifier_key: c.identifierKey,
      computer_name: c.computerName,
    }));

    console.log(`Loaded ${computers.length} computers for testing`);
  });

  it("should handle 410 concurrent requests", async () => {
    const baseUrl = process.env.TEST_BASE_URL || "http://localhost:3000";
    const startTime = Date.now();

    console.log(`Starting ${computers.length} concurrent requests...`);

    // Створюємо масив промісів для всіх запитів
    const requests = computers.map(async (computer, index) => {
      const requestStart = Date.now();

      try {
        const response = await fetch(`${baseUrl}/get_credentials`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Forwarded-For": `127.0.0.${(index % 255) + 1}`,
          },
          body: JSON.stringify(computer),
        });

        const requestTime = Date.now() - requestStart;
        const data = await response.json();

        return {
          success: response.ok,
          status: response.status,
          time: requestTime,
          computer: computer.computer_name,
          hasData: !!data,
        };
      } catch (error) {
        return {
          success: false,
          status: 0,
          time: Date.now() - requestStart,
          computer: computer.computer_name,
          error: error instanceof Error ? error.message : String(error),
        };
      }
    });

    // Виконуємо всі запити паралельно
    const results = await Promise.all(requests);
    const totalTime = Date.now() - startTime;

    // Аналізуємо результати
    const successful = results.filter((r) => r.success);
    const failed = results.filter((r) => !r.success);
    const responseTimes = results.map((r) => r.time);
    const avgTime =
      responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
    const minTime = Math.min(...responseTimes);
    const maxTime = Math.max(...responseTimes);

    // Виводимо статистику
    console.log("\n=== Load Test Results ===");
    console.log(`Total requests: ${results.length}`);
    console.log(`Successful: ${successful.length}`);
    console.log(`Failed: ${failed.length}`);
    console.log(
      `Success rate: ${((successful.length / results.length) * 100).toFixed(
        2
      )}%`
    );
    console.log(`\nTiming:`);
    console.log(`  Total time: ${totalTime}ms`);
    console.log(`  Average response time: ${avgTime.toFixed(2)}ms`);
    console.log(`  Min response time: ${minTime}ms`);
    console.log(`  Max response time: ${maxTime}ms`);
    console.log(
      `  Requests per second: ${((results.length / totalTime) * 1000).toFixed(
        2
      )}`
    );

    // Показуємо перші помилки якщо є
    if (failed.length > 0) {
      console.log(`\n=== First 10 Failures ===`);
      failed.slice(0, 10).forEach((f, i) => {
        console.log(
          `${i + 1}. ${f.computer}: ${f.error || `Status ${f.status}`}`
        );
      });
    }

    // Assertions
    expect(successful.length).toBeGreaterThan(results.length * 0.95); // Мінімум 95% успіху
    expect(avgTime).toBeLessThan(5000); // Середній час відповіді менше 5 секунд
    expect(maxTime).toBeLessThan(10000); // Максимальний час менше 10 секунд
  }, 120000); // Timeout 2 хвилини

  it("should handle requests in batches of 100", async () => {
    const baseUrl = process.env.TEST_BASE_URL || "http://localhost:3000";
    const batchSize = 100;
    const batches = Math.ceil(computers.length / batchSize);

    console.log(`Testing with ${batches} batches of ${batchSize} requests...`);

    const allResults = [];
    const startTime = Date.now();

    for (let i = 0; i < batches; i++) {
      const batchStart = Date.now();
      const batch = computers.slice(i * batchSize, (i + 1) * batchSize);

      const batchRequests = batch.map(async (computer, index) => {
        try {
          const response = await fetch(`${baseUrl}/get_credentials`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(computer),
          });

          const data = await response.json();
          return {
            success: response.ok,
            status: response.status,
          };
        } catch (error) {
          return {
            success: false,
            status: 0,
          };
        }
      });

      const batchResults = await Promise.all(batchRequests);
      allResults.push(...batchResults);

      const batchTime = Date.now() - batchStart;
      const successful = batchResults.filter((r) => r.success).length;

      console.log(
        `  Batch ${i + 1}/${batches}: ${successful}/${
          batch.length
        } successful in ${batchTime}ms`
      );
    }

    const totalTime = Date.now() - startTime;
    const successful = allResults.filter((r) => r.success).length;

    console.log(`\n=== Batch Test Results ===`);
    console.log(`Total: ${successful}/${allResults.length} successful`);
    console.log(`Total time: ${totalTime}ms`);
    console.log(
      `Success rate: ${((successful / allResults.length) * 100).toFixed(2)}%`
    );

    expect(successful).toBeGreaterThan(allResults.length * 0.95);
  }, 180000); // Timeout 3 хвилини
});
