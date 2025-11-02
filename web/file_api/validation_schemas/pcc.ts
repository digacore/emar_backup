import { z } from "zod";
export const PCCDownloadSchema = z.object({
  identifier_key: z.string().min(1),
  computer_name: z.string().min(1),
  pcc_fac_id: z.string().min(1),
});
export type PCCDownloadData = z.infer<typeof PCCDownloadSchema>;
