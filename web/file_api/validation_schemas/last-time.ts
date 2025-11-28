import { z } from "zod";

export const LastTimeSchema = z.object({
  identifier_key: z.string().optional(),
  computer_name: z.string(),
  last_download_time: z.boolean().optional(),
});

export type LastTimeRequest = z.infer<typeof LastTimeSchema>;

export interface LastTimeResponse {
  status: "success" | "fail";
  message: string;
  sftp_host?: string;
  sftp_username?: string;
  sftp_folder_path?: string;
  manager_host?: string;
  msi_version?: string;
  rmcreds?: string;
}
