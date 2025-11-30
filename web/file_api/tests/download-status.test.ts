import { describe, test, expect, beforeAll } from "bun:test";
import { db } from "../database/db";
import { computers } from "../drizzle/schema";
import { eq } from "drizzle-orm";
import type { DownloadStatusResponse } from "../validation_schemas/download-status";

const BASE_URL = "http://localhost:3000";

describe("Download Status Route", () => {
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

  test("should update download status successfully", async () => {
    const response = await fetch(`${BASE_URL}/download_status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        company_name: "Test Company",
        location_name: "Test Location",
        download_status: "success",
        last_time_online: "2025-11-30 10:00:00",
        identifier_key: testComputer.identifier_key,
        last_downloaded: "backup_file.zip",
        last_saved_path: "/backups/backup_file.zip",
      }),
    });

    expect(response.status).toBe(200);

    const data = (await response.json()) as DownloadStatusResponse;
    expect(data.status).toBe("success");
    expect(data.message).toBe("Writing download status to db");
  });

  test("should update download status without optional fields", async () => {
    const response = await fetch(`${BASE_URL}/download_status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        company_name: "Test Company",
        location_name: "Test Location",
        download_status: "in_progress",
        last_time_online: "2025-11-30 11:00:00",
        identifier_key: testComputer.identifier_key,
      }),
    });

    expect(response.status).toBe(200);

    const data = (await response.json()) as DownloadStatusResponse;
    expect(data.status).toBe("success");
  });

  test("should handle error status", async () => {
    const response = await fetch(`${BASE_URL}/download_status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        company_name: "Test Company",
        location_name: "Test Location",
        download_status: "error",
        last_time_online: "2025-11-30 12:00:00",
        identifier_key: testComputer.identifier_key,
        error_message: "Connection timeout",
      }),
    });

    expect(response.status).toBe(200);

    const data = (await response.json()) as DownloadStatusResponse;
    expect(data.status).toBe("success");
  });

  test("should return 400 with non-existent identifier_key", async () => {
    const response = await fetch(`${BASE_URL}/download_status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        company_name: "Test Company",
        location_name: "Test Location",
        download_status: "success",
        last_time_online: "2025-11-30 10:00:00",
        identifier_key: "non-existent-key-12345",
      }),
    });

    expect(response.status).toBe(400);

    const data = (await response.json()) as DownloadStatusResponse;
    expect(data.status).toBe("fail");
    expect(data.message).toBe("Wrong request data. Computer not found.");
  });

  test("should return 400 with missing required field", async () => {
    const response = await fetch(`${BASE_URL}/download_status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        company_name: "Test Company",
        download_status: "success",
        last_time_online: "2025-11-30 10:00:00",
        identifier_key: testComputer.identifier_key,
        // missing location_name
      }),
    });

    expect(response.status).toBe(400);
  });

  test("should return 405 for GET method", async () => {
    const response = await fetch(`${BASE_URL}/download_status`, {
      method: "GET",
    });

    expect(response.status).toBe(405);
  });

  test("should verify timestamp update in database", async () => {
    const beforeTime = new Date();

    await fetch(`${BASE_URL}/download_status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        company_name: "Test Company",
        location_name: "Test Location",
        download_status: "success",
        last_time_online: "2025-11-30 13:00:00",
        identifier_key: testComputer.identifier_key,
      }),
    });

    // Check database was updated
    const updatedComputer = await db.query.computers.findFirst({
      where: eq(computers.identifierKey, testComputer.identifier_key),
      columns: {
        lastTimeOnline: true,
        downloadStatus: true,
      },
    });

    expect(updatedComputer).toBeDefined();
    expect(updatedComputer?.downloadStatus).toBe("success");
    expect(updatedComputer?.lastTimeOnline).toBeDefined();
  });
});
