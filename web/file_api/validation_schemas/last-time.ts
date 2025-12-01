import { z } from "zod";

export const LastTimeSchema = z.object({
  identifier_key: z.string().optional(),
  computer_name: z.string(),
  // Accept boolean (true/false) or string (timestamp) and convert to boolean
  last_download_time: z
    .union([z.boolean(), z.string()])
    .transform((val) => (typeof val === "boolean" ? val : val.length > 0))
    .optional(),
});

export type LastTimeRequest = z.infer<typeof LastTimeSchema>;

export interface LastTimeResponse {
  status: "success" | "fail";
  message: string;
  sftp_host?: string;
  sftp_username?: string;
  sftp_folder_path: string; // Required by Flask Pydantic
  manager_host?: string;
  msi_version?: string;
  rmcreds?: string;
}
