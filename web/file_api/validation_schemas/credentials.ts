import { z } from "zod";

export const GetCredentialsSchema = z.object({
  identifier_key: z.string().min(1),
  computer_name: z.string().min(1),
});

export type GetCredentialsData = z.infer<typeof GetCredentialsSchema>;

export interface ComputerCredentialsInfo {
  status: string;
  message: string;
  host: string | null;
  company_name: string;
  location_name: string;
  additional_locations: string[];
  sftp_username: string | null;
  sftp_password: string | null;
  sftp_folder_path: string | null;
  additional_folder_paths: string[];
  identifier_key: string;
  computer_name: string;
  folder_password: string | null;
  manager_host: string | null;
  device_location: string | null;
  files_checksum: Record<string, any>;
  msi_version: string;
  version: string;
  use_pcc_backup: boolean;
  pcc_fac_id: number | null;
}
