import { describe, it, expect, beforeAll, afterAll } from "bun:test";
import { drizzle } from "drizzle-orm/node-postgres";
import * as schemas from "../drizzle/schema";
import { downloadFromPCC } from "../routes/download-from-pcc";

const db = drizzle(process.env.DATABASE_URL!, { schema: schemas });

// Helper function to create a mock BunRequest
function createMockBunRequest(body: any): any {
  return {
    json: async () => body,
    params: {},
    cookies: {},
  } as any;
}

describe("PCC Download Tests", () => {
  beforeAll(async () => {
    // Setup test data if needed
    console.log("Setting up PCC tests...");
  });

  afterAll(async () => {
    // Cleanup test data if needed
    console.log("Cleaning up PCC tests...");
  });

  describe("downloadFromPCC", () => {
    it("should return correct response", async () => {
      const req = createMockBunRequest({
        identifier_key: "pass identifier here",
        computer_name: "pass computer name here",
        pcc_fac_id: "pass pcc fac id here",
      });
      const res = await downloadFromPCC(req);
      expect(res.status).toBe(200);
      const text = await res.text();
      expect(text).toBeTruthy();
    });
  });
});
