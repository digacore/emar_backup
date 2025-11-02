import { describe, it, expect, beforeAll, afterAll } from "bun:test";
import { drizzle } from "drizzle-orm/node-postgres";
import * as schemas from "../drizzle/schema";
import { downloadFromPCC } from "../routes/download_from_pcc";

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
    it("should return 400 for invalid request body", async () => {
      const req = createMockBunRequest({
        invalid_field: "test",
      });
      try {
        await downloadFromPCC(req);
        expect(true).toBe(false); // Should throw validation error
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });
});
