import { z } from "zod";

export const GetCredentialsSchema = z.object({
  identifier_key: z.string().min(1),
  computer_name: z.string().min(1),
});

export type GetCredentialsData = z.infer<typeof GetCredentialsSchema>;

export interface LocationInfo {
  name: string;
  company_name: string | null;
  total_computers: number;
  total_computers_offline: number;
  primary_computers_offline: number;
  default_sftp_path: string | null;
  pcc_fac_id: number | null;
}

export interface ComputerCredentialsInfo {
  status: string;
  message: string;
  host: string | null;
  company_name: string;
  location_name: string;
  additional_locations: LocationInfo[];
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
  pcc_fac_id: string | null; // Changed from number | null to string | null
}

export interface CredentialsErrorResponse {
  status: "fail";
  message: string;
  rmcreds?: string;
}

export type GetCredentialsResponse =
  | ComputerCredentialsInfo
  | CredentialsErrorResponse;
