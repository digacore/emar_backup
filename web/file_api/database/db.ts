import { drizzle } from "drizzle-orm/node-postgres";
import { Pool } from "pg";
import * as relations from "../drizzle/relations";
import * as schemas from "../drizzle/schema";

// Create a connection pool
export const pool = new Pool({
  connectionString: process.env.DATABASE_URL!,
  // Connection pool settings for high concurrency
  max: 50, // Maximum number of clients in the pool (increased for 410 concurrent)
  min: 10, // Minimum number of clients to keep
  idleTimeoutMillis: 30000, // Close idle clients after 30 seconds
  connectionTimeoutMillis: 30000, // Wait max 30 seconds for connection (increased)
  maxUses: 7500, // Close connection after 7500 queries
  allowExitOnIdle: false, // Don't let pool exit when idle
});

// Handle pool errors
pool.on("error", (err) => {
  console.error("Unexpected error on idle client", err);
});

// Create drizzle instance with the pool
export const db = drizzle(pool, {
  schema: { ...schemas, ...relations },
});

// Graceful shutdown
process.on("SIGTERM", async () => {
  console.log("SIGTERM received, closing database pool...");
  await pool.end();
  process.exit(0);
});

process.on("SIGINT", async () => {
  console.log("SIGINT received, closing database pool...");
  await pool.end();
  process.exit(0);
});
