import { GetCredentialsSchema } from "../validation_schemas/credentials";
import type { ComputerCredentialsInfo } from "../validation_schemas/credentials";
import { db } from "../database/db";
import {
  computers,
  additionalLocations,
  desktopClients,
  clientVersions,
} from "../drizzle/schema";
import { eq, and } from "drizzle-orm";
import { logger } from "../utils/logger";
import { getCurrentTimestamp } from "../utils/timestamp";

export const getCredentials = async (req: Request) => {
  const bodyRaw = await req.json();
  const body = GetCredentialsSchema.parse(bodyRaw);

  logger.info({ computer: body.computer_name }, "Request for credentials");

  // Single query to find computer with all needed relations
  const computer = await db.query.computers.findFirst({
    with: {
      company: true,
      location: true,
    },
    where: and(
      eq(computers.identifierKey, body.identifier_key),
      eq(computers.computerName, body.computer_name),
      eq(computers.isDeleted, false)
    ),
  });

  if (!computer) {
    // Check if computer exists by name only (for better error message)
    const computerByName = await db.query.computers.findFirst({
      where: eq(computers.computerName, body.computer_name),
      columns: { id: true }, // Only fetch ID to minimize data transfer
    });

    let message: string;
    let rmcreds: string | undefined;

    if (computerByName) {
      message = "Wrong id.";
      logger.info(
        { computer: body.computer_name, reason: message },
        "Supplying credentials failed"
      );
    } else {
      message = "Wrong request data. Computer not found.";
      rmcreds = "rmcreds";
      logger.info(
        { computer: body.computer_name, reason: message },
        "Supplying credentials failed. Removing local credentials."
      );
    }

    return new Response(JSON.stringify({ status: "fail", message, rmcreds }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  // Check if computer is activated
  if (!computer.activated) {
    const message = "Computer is not activated.";
    logger.info(
      {
        computer: body.computer_name,
        reason: message,
      },
      "Supplying credentials failed"
    );
    return new Response(JSON.stringify({ status: "fail", message }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  logger.info(
    { computer: computer.computerName },
    "Supplying credentials for computer"
  );

  // Fire-and-forget update (don't wait for it)
  const clientIp =
    req.headers.get("X-Forwarded-For") ||
    req.headers.get("X-Real-IP") ||
    "unknown";

  const timestamp = getCurrentTimestamp();
  logger.info(
    { computerIp: clientIp, lastTimeOnline: timestamp },
    "Updating computer IP and last_time_online in DB"
  );

  db.update(computers)
    .set({
      computerIp: clientIp,
      lastTimeOnline: timestamp,
    })
    .where(eq(computers.id, computer.id))
    .catch((err) =>
      logger.error(
        { err, computer: computer.id },
        "Failed to update computer info"
      )
    );

  // Run all queries in parallel
  const [additionalLocationsList, msi] = await Promise.all([
    // Get additional locations
    db.query.additionalLocations.findMany({
      with: { location: true },
      where: eq(additionalLocations.computerId, computer.id),
    }),
    // Get MSI version
    (async () => {
      if (
        computer.msiVersion === "stable" ||
        computer.msiVersion === "latest"
      ) {
        // Find by flag name - use single query with join, only select version (not blob)
        const result = await db
          .select({
            version: desktopClients.version,
            id: desktopClients.id,
          })
          .from(clientVersions)
          .leftJoin(
            desktopClients,
            eq(desktopClients.flagId, clientVersions.id)
          )
          .where(eq(clientVersions.name, computer.msiVersion))
          .limit(1);
        return result[0]?.version ? { version: result[0].version } : null;
      } else if (computer.msiVersion) {
        // Find by version - only select version field
        return db.query.desktopClients.findFirst({
          where: eq(desktopClients.version, computer.msiVersion),
          columns: { version: true }, // Only fetch version, not blob
        });
      }
      return null;
    })(),
  ]);

  const additionalLocationNames = additionalLocationsList
    .map((al) => al.location?.name)
    .filter((name): name is string => name !== null && name !== undefined);

  // Parse files checksum
  const filesChecksum = computer.filesChecksum
    ? typeof computer.filesChecksum === "string"
      ? JSON.parse(computer.filesChecksum)
      : computer.filesChecksum
    : {};

  // Build credentials info
  const credInfo: ComputerCredentialsInfo = {
    status: "success",
    message: "Supplying credentials",
    host: computer.sftpHost,
    company_name: computer.company?.name || "",
    location_name: computer.location?.name || "",
    additional_locations: additionalLocationNames,
    sftp_username: computer.sftpUsername,
    sftp_password: computer.sftpPassword,
    sftp_folder_path: computer.sftpFolderPath,
    additional_folder_paths: [],
    identifier_key: computer.identifierKey,
    computer_name: computer.computerName,
    folder_password: computer.folderPassword,
    manager_host: computer.managerHost,
    device_location: computer.deviceLocation,
    files_checksum: filesChecksum,
    msi_version: msi?.version || "undefined",
    version: msi?.version || "undefined",
    use_pcc_backup: computer.location?.usePccBackup || false,
    pcc_fac_id: computer.location?.pccFacId
      ? String(computer.location.pccFacId)
      : null,
  };

  return new Response(JSON.stringify(credInfo), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
};
