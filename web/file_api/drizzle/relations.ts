import { relations } from "drizzle-orm/relations";
import { users, systemLogs, companies, pccCreationReports, clientVersions, desktopClients, locationGroups, locationsToGroups, locations, computers, logEvents, usersToGroup, usersToLocation, alertEvents, downloadBackupCalls, companySettingsLinkTable, telemetrySettings, locationSettingsLinkTable, computerSettingsLinkTable, additionalLocations, backupLogs } from "./schema";

export const systemLogsRelations = relations(systemLogs, ({one}) => ({
	user: one(users, {
		fields: [systemLogs.createdById],
		references: [users.id]
	}),
}));

export const usersRelations = relations(users, ({one, many}) => ({
	systemLogs: many(systemLogs),
	usersToGroups: many(usersToGroup),
	usersToLocations: many(usersToLocation),
	company: one(companies, {
		fields: [users.companyId],
		references: [companies.id]
	}),
}));

export const pccCreationReportsRelations = relations(pccCreationReports, ({one}) => ({
	company: one(companies, {
		fields: [pccCreationReports.companyId],
		references: [companies.id]
	}),
}));

export const companiesRelations = relations(companies, ({many}) => ({
	pccCreationReports: many(pccCreationReports),
	locationGroups: many(locationGroups),
	locations: many(locations),
	companySettingsLinkTables: many(companySettingsLinkTable),
	computers: many(computers),
	users: many(users),
}));

export const desktopClientsRelations = relations(desktopClients, ({one}) => ({
	clientVersion: one(clientVersions, {
		fields: [desktopClients.flagId],
		references: [clientVersions.id]
	}),
}));

export const clientVersionsRelations = relations(clientVersions, ({many}) => ({
	desktopClients: many(desktopClients),
}));

export const locationsToGroupsRelations = relations(locationsToGroups, ({one}) => ({
	locationGroup: one(locationGroups, {
		fields: [locationsToGroups.locationGroupId],
		references: [locationGroups.id]
	}),
	location: one(locations, {
		fields: [locationsToGroups.locationId],
		references: [locations.id]
	}),
}));

export const locationGroupsRelations = relations(locationGroups, ({one, many}) => ({
	locationsToGroups: many(locationsToGroups),
	usersToGroups: many(usersToGroup),
	company: one(companies, {
		fields: [locationGroups.companyId],
		references: [companies.id]
	}),
}));

export const locationsRelations = relations(locations, ({one, many}) => ({
	locationsToGroups: many(locationsToGroups),
	usersToLocations: many(usersToLocation),
	alertEvents: many(alertEvents),
	company: one(companies, {
		fields: [locations.companyId],
		references: [companies.id]
	}),
	locationSettingsLinkTables: many(locationSettingsLinkTable),
	additionalLocations: many(additionalLocations),
	computers: many(computers),
}));

export const logEventsRelations = relations(logEvents, ({one}) => ({
	computer: one(computers, {
		fields: [logEvents.computerId],
		references: [computers.id]
	}),
}));

export const computersRelations = relations(computers, ({one, many}) => ({
	logEvents: many(logEvents),
	downloadBackupCalls: many(downloadBackupCalls),
	computerSettingsLinkTables: many(computerSettingsLinkTable),
	additionalLocations: many(additionalLocations),
	backupLogs: many(backupLogs),
	location: one(locations, {
		fields: [computers.locationId],
		references: [locations.id]
	}),
	company: one(companies, {
		fields: [computers.companyId],
		references: [companies.id]
	}),
}));

export const usersToGroupRelations = relations(usersToGroup, ({one}) => ({
	locationGroup: one(locationGroups, {
		fields: [usersToGroup.locationGroupId],
		references: [locationGroups.id]
	}),
	user: one(users, {
		fields: [usersToGroup.userId],
		references: [users.id]
	}),
}));

export const usersToLocationRelations = relations(usersToLocation, ({one}) => ({
	location: one(locations, {
		fields: [usersToLocation.locationId],
		references: [locations.id]
	}),
	user: one(users, {
		fields: [usersToLocation.userId],
		references: [users.id]
	}),
}));

export const alertEventsRelations = relations(alertEvents, ({one}) => ({
	location: one(locations, {
		fields: [alertEvents.locationId],
		references: [locations.id]
	}),
}));

export const downloadBackupCallsRelations = relations(downloadBackupCalls, ({one}) => ({
	computer: one(computers, {
		fields: [downloadBackupCalls.computerId],
		references: [computers.id]
	}),
}));

export const companySettingsLinkTableRelations = relations(companySettingsLinkTable, ({one}) => ({
	company: one(companies, {
		fields: [companySettingsLinkTable.companyId],
		references: [companies.id]
	}),
	telemetrySetting: one(telemetrySettings, {
		fields: [companySettingsLinkTable.telemetrySettingsId],
		references: [telemetrySettings.id]
	}),
}));

export const telemetrySettingsRelations = relations(telemetrySettings, ({many}) => ({
	companySettingsLinkTables: many(companySettingsLinkTable),
	locationSettingsLinkTables: many(locationSettingsLinkTable),
	computerSettingsLinkTables: many(computerSettingsLinkTable),
}));

export const locationSettingsLinkTableRelations = relations(locationSettingsLinkTable, ({one}) => ({
	location: one(locations, {
		fields: [locationSettingsLinkTable.locationId],
		references: [locations.id]
	}),
	telemetrySetting: one(telemetrySettings, {
		fields: [locationSettingsLinkTable.telemetrySettingsId],
		references: [telemetrySettings.id]
	}),
}));

export const computerSettingsLinkTableRelations = relations(computerSettingsLinkTable, ({one}) => ({
	computer: one(computers, {
		fields: [computerSettingsLinkTable.computerId],
		references: [computers.id]
	}),
	telemetrySetting: one(telemetrySettings, {
		fields: [computerSettingsLinkTable.telemetrySettingsId],
		references: [telemetrySettings.id]
	}),
}));

export const additionalLocationsRelations = relations(additionalLocations, ({one}) => ({
	computer: one(computers, {
		fields: [additionalLocations.computerId],
		references: [computers.id]
	}),
	location: one(locations, {
		fields: [additionalLocations.locationId],
		references: [locations.id]
	}),
}));

export const backupLogsRelations = relations(backupLogs, ({one}) => ({
	computer: one(computers, {
		fields: [backupLogs.computerId],
		references: [computers.id]
	}),
}));