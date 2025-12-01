import { z } from "zod";

export const DownloadStatusSchema = z.object({
  company_name: z.string(),
  location_name: z.string(),
  download_status: z.string(),
  last_time_online: z.string(), // datetime as string from client
  identifier_key: z.string(),
  last_downloaded: z.string().optional(),
  last_saved_path: z.string().optional(),
  error_message: z.string().optional(),
});

export const DownloadStatusResponseSchema = z.object({
  status: z.literal("success").or(z.literal("fail")),
  message: z.string(),
});

export type DownloadStatusRequest = z.infer<typeof DownloadStatusSchema>;
export type DownloadStatusResponse = z.infer<
  typeof DownloadStatusResponseSchema
>;
