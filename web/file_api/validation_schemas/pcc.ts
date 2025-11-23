import { z } from "zod";
export const PCCDownloadSchema = z.object({
  identifier_key: z.string().min(1),
  computer_name: z.string().min(1),
  pcc_fac_id: z
    .union([
      z.string().min(1).regex(/^\d+$/, "pcc_fac_id must be a numeric string"),
      z.number().int().positive(),
    ])
    .transform((val) => String(val)),
});
export type PCCDownloadData = z.infer<typeof PCCDownloadSchema>;
