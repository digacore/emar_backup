import { describe, it, expect, beforeAll, afterAll } from "bun:test";
import { drizzle } from "drizzle-orm/node-postgres";
import * as schemas from "../drizzle/schema";
import { getCredentials } from "../routes/get-credentials";

const db = drizzle(process.env.DATABASE_URL!, { schema: schemas });

// Helper function to create a mock BunRequest
function createMockBunRequest(body: any): any {
  return {
    json: async () => body,
    params: {},
    cookies: {},
    headers: new Headers({
      "X-Forwarded-For": "127.0.0.1",
    }),
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

  describe("getCredentials", () => {
    it("should return correct response", async () => {
      const req = createMockBunRequest({
        identifier_key: "cc0f751f-056f-42d3-a73f-02ed02b4eaa9",
        computer_name: "DTC-AM-C6NC264",
      });
      const res = await getCredentials(req);
      expect(res.status).toBe(200);
      const text = await res.text();
      expect(text).toBeTruthy();
    });
  });
});
