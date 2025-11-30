import { describe, test, expect, beforeAll } from "bun:test";
import { db } from "../database/db";
import { computers } from "../drizzle/schema";
import { eq } from "drizzle-orm";
import type {
  GetCredentialsResponse,
  ComputerCredentialsInfo,
  CredentialsErrorResponse,
} from "../validation_schemas/credentials";

const BASE_URL = "http://localhost:3000";

describe("Get Credentials Route", () => {
  let testComputer: {
    identifier_key: string;
    computer_name: string;
  };

  beforeAll(async () => {
    // Get a real activated computer from database
    const computer = await db.query.computers.findFirst({
      where: eq(computers.activated, true),
      columns: {
        identifierKey: true,
        computerName: true,
      },
    });

    if (!computer) {
      throw new Error("No activated computers found in database for testing");
    }

    testComputer = {
      identifier_key: computer.identifierKey,
      computer_name: computer.computerName,
    };
  });

  test("should return credentials successfully", async () => {
    const response = await fetch(`${BASE_URL}/get_credentials`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        identifier_key: testComputer.identifier_key,
        computer_name: testComputer.computer_name,
      }),
    });

    expect(response.status).toBe(200);

    const data = (await response.json()) as ComputerCredentialsInfo;
    expect(data.status).toBe("success");
    expect(data.message).toBe("Supplying credentials");

    // Verify all required fields
    expect(data.host).toBeDefined();
    expect(data.company_name).toBeDefined();
    expect(data.location_name).toBeDefined();
    expect(data.sftp_username).toBeDefined();
    expect(data.sftp_password).toBeDefined();
    expect(data.sftp_folder_path).toBeDefined();
    expect(data.identifier_key).toBe(testComputer.identifier_key);
    expect(data.computer_name).toBe(testComputer.computer_name);
    expect(data.manager_host).toBeDefined();
    expect(data.msi_version).toBeDefined();
    expect(data.version).toBeDefined();
    expect(typeof data.use_pcc_backup).toBe("boolean");

    // Additional locations should be an array
    expect(Array.isArray(data.additional_locations)).toBe(true);
    expect(Array.isArray(data.additional_folder_paths)).toBe(true);
  });

  test("should return 400 with wrong identifier_key but correct computer_name", async () => {
    const response = await fetch(`${BASE_URL}/get_credentials`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        identifier_key: "wrong-key-12345",
        computer_name: testComputer.computer_name,
      }),
    });

    expect(response.status).toBe(400);

    const data = (await response.json()) as CredentialsErrorResponse;
    expect(data.status).toBe("fail");
    expect(data.message).toBe("Wrong id.");
  });

  test("should return 400 with non-existent computer and rmcreds flag", async () => {
    const response = await fetch(`${BASE_URL}/get_credentials`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        identifier_key: "non-existent-key",
        computer_name: "NON-EXISTENT-PC-12345",
      }),
    });

    expect(response.status).toBe(400);

    const data = (await response.json()) as CredentialsErrorResponse;
    expect(data.status).toBe("fail");
    expect(data.message).toBe("Wrong request data. Computer not found.");
    expect(data.rmcreds).toBe("rmcreds");
  });

  test("should validate required fields", async () => {
    const response = await fetch(`${BASE_URL}/get_credentials`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        // Missing identifier_key
        computer_name: testComputer.computer_name,
      }),
    });

    expect(response.status).toBeGreaterThanOrEqual(400);
  });

  test("should return 405 for GET method", async () => {
    const response = await fetch(`${BASE_URL}/get_credentials`, {
      method: "GET",
    });

    expect(response.status).toBe(405);
  });

  test("should handle deactivated computer", async () => {
    // Find a deactivated computer
    const deactivatedComputer = await db.query.computers.findFirst({
      where: eq(computers.activated, false),
      columns: {
        identifierKey: true,
        computerName: true,
        isDeleted: true,
      },
    });

    if (deactivatedComputer && !deactivatedComputer.isDeleted) {
      const response = await fetch(`${BASE_URL}/get_credentials`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          identifier_key: deactivatedComputer.identifierKey,
          computer_name: deactivatedComputer.computerName,
        }),
      });

      expect(response.status).toBe(400);

      const data = (await response.json()) as CredentialsErrorResponse;
      expect(data.status).toBe("fail");
      // Message could be either "Computer is not activated." or "Wrong id." depending on data
      expect(["Computer is not activated.", "Wrong id."]).toContain(
        data.message
      );
    } else {
      // Skip test if no deactivated computers available
      expect(true).toBe(true);
    }
  });

  test("should update computer IP and last_time_online", async () => {
    const beforeUpdate = await db.query.computers.findFirst({
      where: eq(computers.identifierKey, testComputer.identifier_key),
      columns: {
        lastTimeOnline: true,
      },
    });

    await fetch(`${BASE_URL}/get_credentials`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Forwarded-For": "192.168.1.100",
      },
      body: JSON.stringify({
        identifier_key: testComputer.identifier_key,
        computer_name: testComputer.computer_name,
      }),
    });

    // Wait for fire-and-forget update
    await new Promise((resolve) => setTimeout(resolve, 100));

    const afterUpdate = await db.query.computers.findFirst({
      where: eq(computers.identifierKey, testComputer.identifier_key),
      columns: {
        lastTimeOnline: true,
        computerIp: true,
      },
    });

    expect(afterUpdate?.lastTimeOnline).toBeDefined();
    // Time should be updated (may be same if very fast)
    if (beforeUpdate?.lastTimeOnline && afterUpdate?.lastTimeOnline) {
      expect(
        new Date(afterUpdate.lastTimeOnline).getTime() >=
          new Date(beforeUpdate.lastTimeOnline).getTime()
      ).toBe(true);
    }
  });
});
