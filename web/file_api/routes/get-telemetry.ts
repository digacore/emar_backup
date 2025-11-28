import {
  TelemetryRequestIdSchema,
  PrinterInfoSchema,
} from "../validation_schemas/telemetry";
import type {
  TelemetryInfoResponse,
  PrinterInfoResponse,
} from "../validation_schemas/telemetry";
import { db } from "../database/db";
import {
  computers,
  telemetrySettings,
  computerSettingsLinkTable,
  locationSettingsLinkTable,
  companySettingsLinkTable,
} from "../drizzle/schema";
import { eq } from "drizzle-orm";
import { logger } from "../utils/logger";

// Helper function to get telemetry settings with fallback chain
async function getTelemetrySettingsForComputer(
  computerId: number,
  locationId: number | null,
  companyId: number | null
) {
  // 1. Try computer-specific settings
  let linkedTable = await db.query.computerSettingsLinkTable.findFirst({
    where: eq(computerSettingsLinkTable.computerId, computerId),
    columns: { telemetrySettingsId: true },
  });

  if (!linkedTable && locationId) {
    // 2. Try location-specific settings
    linkedTable = await db.query.locationSettingsLinkTable.findFirst({
      where: eq(locationSettingsLinkTable.locationId, locationId),
      columns: { telemetrySettingsId: true },
    });
  }

  if (!linkedTable && companyId) {
    // 3. Try company-specific settings
    linkedTable = await db.query.companySettingsLinkTable.findFirst({
      where: eq(companySettingsLinkTable.companyId, companyId),
      columns: { telemetrySettingsId: true },
    });
  }

  if (!linkedTable) {
    // 4. Get default settings (id=1) or create new one
    let defaultSettings = await db.query.telemetrySettings.findFirst({
      where: eq(telemetrySettings.id, 1),
    });

    if (!defaultSettings) {
      // Create default settings
      const [newSettings] = await db
        .insert(telemetrySettings)
        .values({})
        .returning();
      return newSettings;
    }

    return defaultSettings;
  }

  // Get telemetry settings by linked ID
  if (linkedTable.telemetrySettingsId) {
    const settings = await db.query.telemetrySettings.findFirst({
      where: eq(telemetrySettings.id, linkedTable.telemetrySettingsId),
    });
    return settings;
  }

  return null;
}

export const getTelemetryInfo = async (req: Request) => {
  // GET request with JSON body (Python requests.get(url, json={...}))
  // Body is now readable because index.ts converts GET to POST internally
  let body;
  try {
    const bodyRaw = await req.json();
    body = TelemetryRequestIdSchema.parse(bodyRaw);
  } catch (err) {
    // If no body or invalid JSON, return error
    const message = "identifier_key is required in request body";
    logger.info(
      { reason: message, error: String(err) },
      "Computer telemetry info failed"
    );

    return new Response(
      JSON.stringify({ status: "fail", message } as TelemetryInfoResponse),
      {
        status: 400,
        headers: { "Content-Type": "application/json" },
      }
    );
  }

  if (!body.identifier_key) {
    const message = "identifier_key is required";
    logger.info({ reason: message }, "Computer telemetry info failed");

    return new Response(
      JSON.stringify({ status: "fail", message } as TelemetryInfoResponse),
      {
        status: 400,
        headers: { "Content-Type": "application/json" },
      }
    );
  }

  const computer = await db.query.computers.findFirst({
    where: eq(computers.identifierKey, body.identifier_key),
    columns: {
      id: true,
      locationId: true,
      companyId: true,
    },
  });

  if (!computer) {
    const message = `Computer with such identifier_key: ${body.identifier_key} doesn't exist`;
    logger.info({ reason: message }, "Computer telemetry info failed");

    return new Response(
      JSON.stringify({ status: "fail", message } as TelemetryInfoResponse),
      {
        status: 404,
        headers: { "Content-Type": "application/json" },
      }
    );
  }

  logger.info("Request for telemetry info");

  const telemetrySettingsData = await getTelemetrySettingsForComputer(
    computer.id,
    computer.locationId,
    computer.companyId
  );

  const response: TelemetryInfoResponse = {
    status: "success",
    send_printer_info: telemetrySettingsData?.sendPrinterInfo || false,
  };

  return new Response(JSON.stringify(response), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
};

export const printerInfo = async (req: Request) => {
  const bodyRaw = await req.json();
  const body = PrinterInfoSchema.parse(bodyRaw);

  logger.info("Printer info update request");

  const computer = await db.query.computers.findFirst({
    where: eq(computers.identifierKey, body.identifier_key),
    columns: { id: true },
  });

  if (!computer) {
    const message = "Wrong request data. Computer not found.";
    logger.info({ reason: message }, "Printer info update failed");

    return new Response(
      JSON.stringify({ status: "fail", message } as PrinterInfoResponse),
      {
        status: 400,
        headers: { "Content-Type": "application/json" },
      }
    );
  }

  // Map printer status codes
  let printerStatus: "NORMAL" | "OFFLINE" | "UNKNOWN" = "UNKNOWN";
  switch (body.printer_info.PrinterStatus) {
    case 0:
      printerStatus = "NORMAL";
      break;
    case 128:
      printerStatus = "OFFLINE";
      break;
    default:
      printerStatus = "UNKNOWN";
  }

  // Format timestamp without milliseconds
  const now = new Date().toISOString().replace("T", " ").substring(0, 19);

  // Fire-and-forget update for speed
  db.update(computers)
    .set({
      printerName: body.printer_info.Name,
      printerStatus: printerStatus,
      printerStatusTimestamp: now,
    })
    .where(eq(computers.id, computer.id))
    .catch((err) =>
      logger.error(
        { err, computer: computer.id },
        "Failed to update printer info"
      )
    );

  logger.info("Printer info updated successfully");

  const response: PrinterInfoResponse = {
    status: "success",
    message: "Writing printer info to db",
  };

  return new Response(JSON.stringify(response), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
};
