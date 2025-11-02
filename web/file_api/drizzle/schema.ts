import {
  pgTable,
  foreignKey,
  serial,
  timestamp,
  integer,
  varchar,
  unique,
  text,
  json,
  boolean,
  pgEnum,
  customType,
} from "drizzle-orm/pg-core";
// Custom type for PostgreSQL bytea
const bytea = customType<{ data: Buffer; notNull: false; default: false }>({
  dataType() {
    return "bytea";
  },
  toDriver(value: Buffer): Buffer {
    return value;
  },
});

export const alerteventtype = pgEnum("alerteventtype", [
  "PRIMARY_COMPUTER_DOWN",
  "CRITICAL_ALERT",
]);
export const backuplogtype = pgEnum("backuplogtype", [
  "WITH_DOWNLOADS_PERIOD",
  "NO_DOWNLOADS_PERIOD",
]);
export const creationreportstatus = pgEnum("creationreportstatus", [
  "WAITING",
  "APPROVED",
  "REJECTED",
]);
export const devicerole = pgEnum("devicerole", ["PRIMARY", "ALTERNATE"]);
export const devicetype = pgEnum("devicetype", ["LAPTOP", "DESKTOP"]);
export const locationstatus = pgEnum("locationstatus", [
  "ONLINE",
  "ONLINE_PRIMARY_OFFLINE",
  "OFFLINE",
]);
export const logtype = pgEnum("logtype", [
  "HEARTBEAT",
  "BACKUP_DOWNLOAD",
  "CLIENT_UPGRADE",
  "CLIENT_ERROR",
  "STATUS_GREEN",
  "STATUS_YELLOW",
  "STATUS_RED",
  "SPECIAL_STATUS",
]);
export const printerstatus = pgEnum("printerstatus", [
  "NORMAL",
  "OFFLINE",
  "UNKNOWN",
]);
export const scanstatus = pgEnum("scanstatus", [
  "IN_PROGRESS",
  "SUCCEED",
  "FAILED",
]);
export const systemlogtype = pgEnum("systemlogtype", [
  "USER_CREATED",
  "USER_UPDATED",
  "USER_DELETED",
  "COMPUTER_CREATED",
  "COMPUTER_UPDATED",
  "COMPUTER_DELETED",
  "COMPANY_CREATED",
  "COMPANY_UPDATED",
  "COMPANY_DELETED",
  "LOCATION_CREATED",
  "LOCATION_UPDATED",
  "LOCATION_DELETED",
  "ALERT_CREATED",
  "ALERT_UPDATED",
  "ALERT_DELETED",
]);
export const userrole = pgEnum("userrole", ["ADMIN", "USER"]);

export const systemLogs = pgTable(
  "system_logs",
  {
    id: serial().primaryKey().notNull(),
    logType: systemlogtype("log_type").notNull(),
    createdAt: timestamp("created_at", { mode: "string" }).notNull(),
    objectId: integer("object_id").notNull(),
    objectName: varchar("object_name", { length: 128 }).notNull(),
    objectUrl: varchar("object_url", { length: 256 }).notNull(),
    createdById: integer("created_by_id"),
  },
  (table) => [
    foreignKey({
      columns: [table.createdById],
      foreignColumns: [users.id],
      name: "system_logs_created_by_id_fkey",
    }),
  ]
);

export const pccAccessTokens = pgTable(
  "pcc_access_tokens",
  {
    id: serial().primaryKey().notNull(),
    token: varchar({ length: 64 }).notNull(),
    expiresIn: integer("expires_in").notNull(),
    createdAt: timestamp("created_at", { mode: "string" }).defaultNow(),
  },
  (table) => [unique("pcc_access_tokens_token_key").on(table.token)]
);

export const pccActivationsScans = pgTable("pcc_activations_scans", {
  id: serial().primaryKey().notNull(),
  error: text(),
  status: scanstatus().notNull(),
  createdAt: timestamp("created_at", { mode: "string" }).defaultNow().notNull(),
  finishedAt: timestamp("finished_at", { mode: "string" }),
});

export const pccCreationReports = pgTable(
  "pcc_creation_reports",
  {
    id: serial().primaryKey().notNull(),
    data: json(),
    companyId: integer("company_id"),
    companyName: varchar("company_name", { length: 255 }).notNull(),
    createdAt: timestamp("created_at", { mode: "string" })
      .defaultNow()
      .notNull(),
    status: creationreportstatus().notNull(),
    statusChangedAt: timestamp("status_changed_at", { mode: "string" }),
  },
  (table) => [
    foreignKey({
      columns: [table.companyId],
      foreignColumns: [companies.id],
      name: "fk_company_id_companies",
    }),
  ]
);

export const desktopClients = pgTable(
  "desktop_clients",
  {
    mimetype: varchar({ length: 255 }).notNull(),
    filename: varchar({ length: 255 }).notNull(),
    blob: bytea("blob").notNull(),
    size: integer().notNull(),
    id: serial().primaryKey().notNull(),
    name: varchar({ length: 64 }).notNull(),
    version: varchar({ length: 64 }),
    description: varchar({ length: 512 }),
    createdAt: timestamp("created_at", { mode: "string" }),
    flagId: integer("flag_id"),
  },
  (table) => [
    foreignKey({
      columns: [table.flagId],
      foreignColumns: [clientVersions.id],
      name: "fkey_desktop_clients_flag_id",
    }).onDelete("cascade"),
    unique("desktop_clients_name_key").on(table.name),
  ]
);

export const pccDailyRequests = pgTable(
  "pcc_daily_requests",
  {
    id: serial().primaryKey().notNull(),
    requestsCount: integer("requests_count").notNull(),
    resetTime: timestamp("reset_time", { mode: "string" }).notNull(),
  },
  (table) => [unique("pcc_daily_requests_reset_time_key").on(table.resetTime)]
);

export const locationsToGroups = pgTable(
  "locations_to_groups",
  {
    id: serial().primaryKey().notNull(),
    locationId: integer("location_id").notNull(),
    locationGroupId: integer("location_group_id").notNull(),
  },
  (table) => [
    foreignKey({
      columns: [table.locationGroupId],
      foreignColumns: [locationGroups.id],
      name: "locations_to_groups_location_group_id_fkey",
    }),
    foreignKey({
      columns: [table.locationId],
      foreignColumns: [locations.id],
      name: "locations_to_groups_location_id_fkey",
    }),
    unique("locations_to_groups_location_id_key").on(table.locationId),
  ]
);

export const alembicVersion = pgTable("alembic_version", {
  versionNum: varchar("version_num", { length: 32 }).primaryKey().notNull(),
});

export const clientVersions = pgTable(
  "client_versions",
  {
    id: serial().primaryKey().notNull(),
    name: varchar({ length: 64 }).notNull(),
    createdAt: timestamp("created_at", { mode: "string" }),
  },
  (table) => [unique("client_versions_name_key").on(table.name)]
);

export const logEvents = pgTable(
  "log_events",
  {
    id: serial().primaryKey().notNull(),
    logType: logtype("log_type").notNull(),
    createdAt: timestamp("created_at", { mode: "string" }),
    data: varchar({ length: 128 }).default(""),
    computerId: integer("computer_id"),
  },
  (table) => [
    foreignKey({
      columns: [table.computerId],
      foreignColumns: [computers.id],
      name: "log_events_computer_id_fkey",
    }),
  ]
);

export const usersToGroup = pgTable(
  "users_to_group",
  {
    id: serial().primaryKey().notNull(),
    userId: integer("user_id").notNull(),
    locationGroupId: integer("location_group_id").notNull(),
  },
  (table) => [
    foreignKey({
      columns: [table.locationGroupId],
      foreignColumns: [locationGroups.id],
      name: "users_to_group_location_group_id_fkey",
    }),
    foreignKey({
      columns: [table.userId],
      foreignColumns: [users.id],
      name: "users_to_group_user_id_fkey",
    }),
    unique("users_to_group_user_id_key").on(table.userId),
  ]
);

export const usersToLocation = pgTable(
  "users_to_location",
  {
    id: serial().primaryKey().notNull(),
    userId: integer("user_id").notNull(),
    locationId: integer("location_id").notNull(),
  },
  (table) => [
    foreignKey({
      columns: [table.locationId],
      foreignColumns: [locations.id],
      name: "users_to_location_location_id_fkey",
    }),
    foreignKey({
      columns: [table.userId],
      foreignColumns: [users.id],
      name: "users_to_location_user_id_fkey",
    }),
    unique("users_to_location_user_id_key").on(table.userId),
  ]
);

export const alertEvents = pgTable(
  "alert_events",
  {
    id: serial().primaryKey().notNull(),
    locationId: integer("location_id").notNull(),
    alertType: alerteventtype("alert_type").notNull(),
    createdAt: timestamp("created_at", { mode: "string" }).notNull(),
  },
  (table) => [
    foreignKey({
      columns: [table.locationId],
      foreignColumns: [locations.id],
      name: "alert_events_location_id_fkey",
    }),
  ]
);

export const downloadBackupCalls = pgTable(
  "download_backup_calls",
  {
    id: serial().primaryKey().notNull(),
    computerId: integer("computer_id").notNull(),
    createdAt: timestamp("created_at", { mode: "string" }).notNull(),
  },
  (table) => [
    foreignKey({
      columns: [table.computerId],
      foreignColumns: [computers.id],
      name: "download_backup_calls_computer_id_fkey",
    }),
  ]
);

export const locationGroups = pgTable(
  "location_groups",
  {
    id: serial().primaryKey().notNull(),
    companyId: integer("company_id").notNull(),
    name: varchar({ length: 64 }).notNull(),
    deletedAt: timestamp("deleted_at", { mode: "string" }),
    createdAt: timestamp("created_at", { mode: "string" }).defaultNow(),
    isDeleted: boolean("is_deleted").default(false),
  },
  (table) => [
    foreignKey({
      columns: [table.companyId],
      foreignColumns: [companies.id],
      name: "location_groups_company_id_fkey",
    }).onDelete("cascade"),
    unique("unique_location_group_per_company").on(table.companyId, table.name),
  ]
);

export const locations = pgTable(
  "locations",
  {
    id: serial().primaryKey().notNull(),
    name: varchar({ length: 64 }).notNull(),
    createdAt: timestamp("created_at", { mode: "string" }),
    computersPerLocation: integer("computers_per_location"),
    computersOffline: integer("computers_offline"),
    computersOnline: integer("computers_online"),
    defaultSftpPath: varchar("default_sftp_path", { length: 256 }),
    pccFacId: integer("pcc_fac_id"),
    usePccBackup: boolean("use_pcc_backup").default(false).notNull(),
    createdFromPcc: boolean("created_from_pcc").default(false).notNull(),
    companyId: integer("company_id").notNull(),
    status: locationstatus(),
    isDeleted: boolean("is_deleted").default(false),
    deletedAt: timestamp("deleted_at", { mode: "string" }),
    activated: boolean().default(true).notNull(),
    deactivatedAt: timestamp("deactivated_at", { mode: "string" }),
  },
  (table) => [
    foreignKey({
      columns: [table.companyId],
      foreignColumns: [companies.id],
      name: "fkey_locations_company_id",
    }),
    unique("unique_location_per_company").on(table.name, table.companyId),
  ]
);

export const companySettingsLinkTable = pgTable(
  "company_settings_link_table",
  {
    id: serial().primaryKey().notNull(),
    companyId: integer("company_id"),
    telemetrySettingsId: integer("telemetry_settings_id"),
  },
  (table) => [
    foreignKey({
      columns: [table.companyId],
      foreignColumns: [companies.id],
      name: "company_settings_link_table_company_id_fkey",
    }),
    foreignKey({
      columns: [table.telemetrySettingsId],
      foreignColumns: [telemetrySettings.id],
      name: "company_settings_link_table_telemetry_settings_id_fkey",
    }),
  ]
);

export const telemetrySettings = pgTable("telemetry_settings", {
  id: serial().primaryKey().notNull(),
  sendPrinterInfo: boolean("send_printer_info"),
  sendAgentLogs: boolean("send_agent_logs"),
});

export const locationSettingsLinkTable = pgTable(
  "location_settings_link_table",
  {
    id: serial().primaryKey().notNull(),
    locationId: integer("location_id"),
    telemetrySettingsId: integer("telemetry_settings_id"),
  },
  (table) => [
    foreignKey({
      columns: [table.locationId],
      foreignColumns: [locations.id],
      name: "location_settings_link_table_location_id_fkey",
    }),
    foreignKey({
      columns: [table.telemetrySettingsId],
      foreignColumns: [telemetrySettings.id],
      name: "location_settings_link_table_telemetry_settings_id_fkey",
    }),
  ]
);

export const computerSettingsLinkTable = pgTable(
  "computer_settings_link_table",
  {
    id: serial().primaryKey().notNull(),
    computerId: integer("computer_id"),
    telemetrySettingsId: integer("telemetry_settings_id"),
  },
  (table) => [
    foreignKey({
      columns: [table.computerId],
      foreignColumns: [computers.id],
      name: "computer_settings_link_table_computer_id_fkey",
    }),
    foreignKey({
      columns: [table.telemetrySettingsId],
      foreignColumns: [telemetrySettings.id],
      name: "computer_settings_link_table_telemetry_settings_id_fkey",
    }),
  ]
);

export const additionalLocations = pgTable(
  "additional_locations",
  {
    id: serial().primaryKey().notNull(),
    computerId: integer("computer_id"),
    locationId: integer("location_id"),
  },
  (table) => [
    foreignKey({
      columns: [table.computerId],
      foreignColumns: [computers.id],
      name: "additional_locations_computer_id_fkey",
    }),
    foreignKey({
      columns: [table.locationId],
      foreignColumns: [locations.id],
      name: "additional_locations_location_id_fkey",
    }),
  ]
);

export const backupLogs = pgTable(
  "backup_logs",
  {
    id: serial().primaryKey().notNull(),
    backupLogType: backuplogtype("backup_log_type").notNull(),
    startTime: timestamp("start_time", { mode: "string" }).notNull(),
    endTime: timestamp("end_time", { mode: "string" }).notNull(),
    error: varchar({ length: 1024 }).default(""),
    notes: varchar({ length: 1024 }).default(""),
    computerId: integer("computer_id"),
  },
  (table) => [
    foreignKey({
      columns: [table.computerId],
      foreignColumns: [computers.id],
      name: "backup_logs_computer_id_fkey",
    }),
  ]
);

export const companies = pgTable(
  "companies",
  {
    id: serial().primaryKey().notNull(),
    name: varchar({ length: 64 }).notNull(),
    createdAt: timestamp("created_at", { mode: "string" }),
    locationsPerCompany: integer("locations_per_company"),
    totalComputers: integer("total_computers"),
    computersOffline: integer("computers_offline"),
    computersOnline: integer("computers_online"),
    defaultSftpUsername: varchar("default_sftp_username", { length: 128 }),
    defaultSftpPassword: varchar("default_sftp_password", { length: 128 }),
    pccOrgId: varchar("pcc_org_id", { length: 128 }),
    createdFromPcc: boolean("created_from_pcc").default(false).notNull(),
    isGlobal: boolean("is_global").default(false).notNull(),
    isDeleted: boolean("is_deleted").default(false),
    deletedAt: timestamp("deleted_at", { mode: "string" }),
    isTrial: boolean("is_trial").default(false).notNull(),
    activated: boolean().default(true).notNull(),
    deactivatedAt: timestamp("deactivated_at", { mode: "string" }),
    computersMaxCount: integer("computers_max_count").default(1),
  },
  (table) => [unique("companies_name_key").on(table.name)]
);

export const computers = pgTable(
  "computers",
  {
    id: serial().primaryKey().notNull(),
    computerName: varchar("computer_name", { length: 64 }).notNull(),
    type: varchar({ length: 128 }),
    activated: boolean().notNull(),
    createdAt: timestamp("created_at", { mode: "string" }),
    sftpHost: varchar("sftp_host", { length: 128 }),
    sftpUsername: varchar("sftp_username", { length: 64 }),
    sftpPassword: varchar("sftp_password", { length: 128 }),
    sftpFolderPath: varchar("sftp_folder_path", { length: 256 }),
    folderPassword: varchar("folder_password", { length: 128 }),
    downloadStatus: varchar("download_status", { length: 64 }),
    lastDownloadTime: timestamp("last_download_time", { mode: "string" }),
    lastTimeOnline: timestamp("last_time_online", { mode: "string" }),
    identifierKey: varchar("identifier_key", { length: 128 }).notNull(),
    managerHost: varchar("manager_host", { length: 256 }),
    lastDownloaded: varchar("last_downloaded", { length: 256 }),
    filesChecksum: json("files_checksum"),
    msiVersion: varchar("msi_version", { length: 64 }),
    currentMsiVersion: varchar("current_msi_version", { length: 64 }),
    computerIp: varchar("computer_ip", { length: 128 }),
    logsEnabled: boolean("logs_enabled").default(true),
    lastSavedPath: varchar("last_saved_path", { length: 256 }),
    lastTimeLogsEnabled: timestamp("last_time_logs_enabled", {
      mode: "string",
    }),
    lastTimeLogsDisabled: timestamp("last_time_logs_disabled", {
      mode: "string",
    }),
    locationId: integer("location_id"),
    companyId: integer("company_id"),
    deviceType: devicetype("device_type"),
    deviceRole: devicerole("device_role").default("PRIMARY").notNull(),
    isDeleted: boolean("is_deleted").default(false),
    deletedAt: timestamp("deleted_at", { mode: "string" }),
    deactivatedAt: timestamp("deactivated_at", { mode: "string" }),
    printerName: varchar("printer_name", { length: 128 }),
    printerStatus: printerstatus("printer_status").default("UNKNOWN"),
    printerStatusTimestamp: timestamp("printer_status_timestamp", {
      mode: "string",
    }),
    sftpPort: integer("sftp_port").default(22),
    additionalSftpFolderPaths: varchar("additional_sftp_folder_paths", {
      length: 256,
    }),
    notes: text(),
    deviceLocation: varchar("device_location", { length: 64 }),
  },
  (table) => [
    foreignKey({
      columns: [table.locationId],
      foreignColumns: [locations.id],
      name: "computers_location_id_fkey",
    }),
    foreignKey({
      columns: [table.companyId],
      foreignColumns: [companies.id],
      name: "fkey_computers_company_id",
    }),
    unique("computers_computer_name_key").on(table.computerName),
  ]
);

export const users = pgTable(
  "users",
  {
    id: serial().primaryKey().notNull(),
    username: varchar({ length: 64 }).notNull(),
    email: varchar({ length: 256 }).notNull(),
    passwordHash: varchar("password_hash", { length: 256 }).notNull(),
    activated: boolean().notNull(),
    createdAt: timestamp("created_at", { mode: "string" }),
    lastTimeOnline: timestamp("last_time_online", { mode: "string" }),
    companyId: integer("company_id").notNull(),
    role: userrole().default("ADMIN").notNull(),
    isDeleted: boolean("is_deleted").default(false),
    deletedAt: timestamp("deleted_at", { mode: "string" }),
    deactivatedAt: timestamp("deactivated_at", { mode: "string" }),
    receiveAlertEmails: boolean("receive_alert_emails"),
    receiveSummariesEmails: boolean("receive_summaries_emails"),
    receiveDeviceTestEmails: boolean("receive_device_test_emails"),
  },
  (table) => [
    foreignKey({
      columns: [table.companyId],
      foreignColumns: [companies.id],
      name: "fk_user_company",
    }),
    unique("users_username_key").on(table.username),
    unique("users_email_key").on(table.email),
  ]
);
