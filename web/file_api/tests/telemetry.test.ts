import { describe, test, expect, beforeAll } from "bun:test";
import { db } from "../database/db";
import { computers } from "../drizzle/schema";
import { eq } from "drizzle-orm";
import type {
  TelemetryInfoResponse,
  PrinterInfoResponse,
} from "../validation_schemas/telemetry";

const BASE_URL = "http://localhost:3000";

describe("Telemetry Routes", () => {
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

  describe("GET /get_telemetry_info", () => {
    test("should return telemetry settings successfully", async () => {
      const response = await fetch(
        `${BASE_URL}/get_telemetry_info?identifier_key=${testComputer.identifier_key}`,
        {
          method: "GET",
        }
      );

      expect(response.status).toBe(200);

      const data = (await response.json()) as TelemetryInfoResponse;
      expect(data.status).toBe("success");
      expect(data.send_printer_info).toBeDefined();
      expect(typeof data.send_printer_info).toBe("boolean");
    });

    test("should return 404 for non-existent computer", async () => {
      const response = await fetch(
        `${BASE_URL}/get_telemetry_info?identifier_key=wrong-key-12345`,
        {
          method: "GET",
        }
      );

      expect(response.status).toBe(404);

      const data = (await response.json()) as TelemetryInfoResponse;
      expect(data.status).toBe("fail");
      expect(data.message).toContain("doesn't exist");
    });

    test("should handle missing identifier_key parameter", async () => {
      const response = await fetch(`${BASE_URL}/get_telemetry_info`, {
        method: "GET",
      });

      // Should fail validation
      expect(response.status).toBeGreaterThanOrEqual(400);
    });

    test("should return 405 for POST method", async () => {
      const response = await fetch(`${BASE_URL}/get_telemetry_info`, {
        method: "POST",
      });

      expect(response.status).toBe(405);
    });
  });

  describe("POST /printer_info", () => {
    test("should update printer info with NORMAL status", async () => {
      const response = await fetch(`${BASE_URL}/printer_info`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          identifier_key: testComputer.identifier_key,
          printer_info: {
            Name: "Test Printer Normal",
            PrinterStatus: 0,
          },
        }),
      });

      expect(response.status).toBe(200);

      const data = (await response.json()) as PrinterInfoResponse;
      expect(data.status).toBe("success");
      expect(data.message).toBe("Writing printer info to db");
    });

    test("should update printer info with OFFLINE status", async () => {
      const response = await fetch(`${BASE_URL}/printer_info`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          identifier_key: testComputer.identifier_key,
          printer_info: {
            Name: "Test Printer Offline",
            PrinterStatus: 128,
          },
        }),
      });

      expect(response.status).toBe(200);

      const data = (await response.json()) as PrinterInfoResponse;
      expect(data.status).toBe("success");
    });

    test("should update printer info with UNKNOWN status", async () => {
      const response = await fetch(`${BASE_URL}/printer_info`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          identifier_key: testComputer.identifier_key,
          printer_info: {
            Name: "Test Printer Unknown",
            PrinterStatus: 999,
          },
        }),
      });

      expect(response.status).toBe(200);

      const data = (await response.json()) as PrinterInfoResponse;
      expect(data.status).toBe("success");
    });

    test("should return 400 for non-existent computer", async () => {
      const response = await fetch(`${BASE_URL}/printer_info`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          identifier_key: "wrong-key-12345",
          printer_info: {
            Name: "Test Printer",
            PrinterStatus: 0,
          },
        }),
      });

      expect(response.status).toBe(400);

      const data = (await response.json()) as PrinterInfoResponse;
      expect(data.status).toBe("fail");
      expect(data.message).toBe("Wrong request data. Computer not found.");
    });

    test("should validate required fields", async () => {
      const response = await fetch(`${BASE_URL}/printer_info`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          identifier_key: testComputer.identifier_key,
          // Missing printer_info
        }),
      });

      expect(response.status).toBeGreaterThanOrEqual(400);
    });

    test("should return 405 for GET method", async () => {
      const response = await fetch(`${BASE_URL}/printer_info`, {
        method: "GET",
      });

      expect(response.status).toBe(405);
    });
  });

  describe("Printer Info Database Verification", () => {
    test("should verify printer info is stored in database", async () => {
      const testPrinterName = `Test Printer ${Date.now()}`;

      // Update printer info
      await fetch(`${BASE_URL}/printer_info`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          identifier_key: testComputer.identifier_key,
          printer_info: {
            Name: testPrinterName,
            PrinterStatus: 0,
          },
        }),
      });

      // Wait a bit for fire-and-forget update to complete
      await new Promise((resolve) => setTimeout(resolve, 100));

      // Verify in database
      const computer = await db.query.computers.findFirst({
        where: eq(computers.identifierKey, testComputer.identifier_key),
        columns: {
          printerName: true,
          printerStatus: true,
          printerStatusTimestamp: true,
        },
      });

      expect(computer).toBeDefined();
      expect(computer?.printerName).toBe(testPrinterName);
      expect(computer?.printerStatus).toBe("NORMAL");
      expect(computer?.printerStatusTimestamp).toBeDefined();
    });
  });
});
