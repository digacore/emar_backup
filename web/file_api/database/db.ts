import { drizzle } from "drizzle-orm/node-postgres";
import * as relations from "../drizzle/relations";
import * as schemas from "../drizzle/schema";

export const db = drizzle(process.env.DATABASE_URL!, {
  schema: { ...schemas, ...relations },
});
