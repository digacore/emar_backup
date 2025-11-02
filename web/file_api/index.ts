import "dotenv/config";
import { drizzle } from "drizzle-orm/node-postgres";

import { users } from "./drizzle/schema.ts";
import { downloadFromPCC } from "./routes/download-from-pcc.ts";

const db = drizzle(process.env.DATABASE_URL!);

async function main() {
  const allUsers = await db.select().from(users);
  console.log("Getting all users from the database: ", allUsers);
}

main();
const server = Bun.serve({
  // `routes` requires Bun v1.2.3+
  routes: {
    "/download_from_pcc": (req) => {
      if (req.method === "POST") {
        return downloadFromPCC(req);
      } else {
        return new Response("Method Not Allowed", { status: 405 });
      }
    },
  },

  // (optional) fallback for unmatched routes:
  // Required if Bun's version < 1.2.3
  fetch(req) {
    return new Response("Not Found", { status: 404 });
  },
});

console.log(`Server running at ${server.url}`);
