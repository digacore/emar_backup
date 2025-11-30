import { describe, test, expect, beforeAll } from "bun:test";
import { db } from "../database/db";
import { computers } from "../drizzle/schema";
import { eq } from "drizzle-orm";
import type { LastTimeResponse } from "../validation_schemas/last-time";

const BASE_URL = "http://localhost:3000";

describe("Last Time Route", () => {
  let testComputer: {
    identifier_key: string;
    computer_name: string;
  };

  beforeAll(async () => {
    // Get a real computer from database
    const computer = await db.query.computers.findFirst({
      where: eq(computers.isDeleted, false),
      columns: {
        identifierKey: true,
        computerName: true,
      },
    });

    if (!computer) {
      throw new Error("No computers found in database for testing");
    }

    testComputer = {
      identifier_key: computer.identifierKey,
      computer_name: computer.computerName,
    };
  });

  test("should update last_time_online successfully", async () => {
    const response = await fetch(`${BASE_URL}/last_time`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        identifier_key: testComputer.identifier_key,
        computer_name: testComputer.computer_name,
      }),
    });

    expect(response.status).toBe(200);

    const data = (await response.json()) as LastTimeResponse;
    expect(data.status).toBe("success");
    expect(data.message).toBe("Writing time to db");
    expect(data.sftp_host).toBeDefined();
    expect(data.sftp_username).toBeDefined();
    expect(data.manager_host).toBeDefined();
    expect(data.msi_version).toBeDefined();
  });

  test("should update both last_time_online and last_download_time", async () => {
    const response = await fetch(`${BASE_URL}/last_time`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        identifier_key: testComputer.identifier_key,
        computer_name: testComputer.computer_name,
        last_download_time: true,
      }),
    });

    expect(response.status).toBe(200);

    const data = (await response.json()) as LastTimeResponse;
    expect(data.status).toBe("success");
  });

  test("should return 400 with wrong identifier_key", async () => {
    const response = await fetch(`${BASE_URL}/last_time`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        identifier_key: "wrong-key-12345",
        computer_name: testComputer.computer_name,
      }),
    });

    expect(response.status).toBe(400);

    const data = (await response.json()) as LastTimeResponse;
    expect(data.status).toBe("fail");
    expect(data.message).toBe("Wrong id.");
  });

  test("should return 400 with non-existent computer and rmcreds flag", async () => {
    const response = await fetch(`${BASE_URL}/last_time`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        identifier_key: "non-existent-key",
        computer_name: "NON-EXISTENT-PC",
      }),
    });

    expect(response.status).toBe(400);

    const data = (await response.json()) as LastTimeResponse;
    expect(data.status).toBe("fail");
    expect(data.message).toBe("Wrong request data. Computer not found.");
    expect(data.rmcreds).toBe("rmcreds");
  });

  test("should handle missing identifier_key (search only by name)", async () => {
    const response = await fetch(`${BASE_URL}/last_time`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        computer_name: testComputer.computer_name,
      }),
    });

    expect(response.status).toBe(400);
    const data = (await response.json()) as LastTimeResponse;
    expect(data.status).toBe("fail");
  });

  test("should return 405 for GET method", async () => {
    const response = await fetch(`${BASE_URL}/last_time`, {
      method: "GET",
    });

    expect(response.status).toBe(405);
  });
});
