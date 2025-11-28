import { z } from "zod";

export const TelemetryRequestIdSchema = z.object({
  identifier_key: z.string().nullable(),
});

export type TelemetryRequestId = z.infer<typeof TelemetryRequestIdSchema>;

export interface TelemetryInfoResponse {
  status: "success" | "fail";
  message?: string;
  send_printer_info?: boolean;
}

export const PrinterInfoDataSchema = z.object({
  Name: z.string(),
  PrinterStatus: z.number(),
});

export const PrinterInfoSchema = z.object({
  identifier_key: z.string(),
  printer_info: PrinterInfoDataSchema,
});

export type PrinterInfo = z.infer<typeof PrinterInfoSchema>;

export interface PrinterInfoResponse {
  status: "success" | "fail";
  message: string;
}
