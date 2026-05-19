import "dotenv/config";
import { downloadFromPCC } from "./routes/download-from-pcc.ts";
import { getCredentials } from "./routes/get-credentials.ts";
import { lastTime } from "./routes/last-time.ts";
import { getTelemetryInfo, printerInfo } from "./routes/get-telemetry.ts";
import { downloadStatus } from "./routes/download-status.ts";
import { healthCheck } from "./routes/health.ts";
import { logger } from "./utils/logger";

if (!process.env.DATABASE_URL) {
  logger.fatal("DATABASE_URL is not set. file_api cannot start.");
  process.exit(1);
}

const server = Bun.serve({
  // `routes` requires Bun v1.2.3+
  // TODO: add downloads_info:files_checksum route
  routes: {
    "/health": (req) => {
      if (req.method === "GET") {
        return healthCheck();
      }
      return new Response("Method Not Allowed", { status: 405 });
    },
    "/download_from_pcc": (req) => {
      if (req.method === "POST") {
        return downloadFromPCC(req);
      } else {
        return new Response("Method Not Allowed", { status: 405 });
      }
    },
    "/get_credentials": (req) => {
      if (req.method === "POST") {
        return getCredentials(req);
      } else {
        return new Response("Method Not Allowed", { status: 405 });
      }
    },
    "/last_time": (req) => {
      if (req.method === "POST") {
        return lastTime(req);
      } else {
        return new Response("Method Not Allowed", { status: 405 });
      }
    },
    // /get_telemetry_info handled in fallback fetch() due to GET+body workaround
    "/printer_info": (req) => {
      if (req.method === "POST") {
        return printerInfo(req);
      } else {
        return new Response("Method Not Allowed", { status: 405 });
      }
    },
    "/download_status": (req) => {
      if (req.method === "POST") {
        return downloadStatus(req);
      } else {
        return new Response("Method Not Allowed", { status: 405 });
      }
    },
  },

  // (optional) fallback for unmatched routes:
  // Required if Bun's version < 1.2.3
  async fetch(req) {
    const url = new URL(req.url);

    // Special handling for /get_telemetry_info
    // Nginx will convert GET (with body) → POST before sending to Bun
    // So we accept POST here
    if (url.pathname === "/get_telemetry_info") {
      if (req.method === "POST") {
        return getTelemetryInfo(req);
      } else if (req.method === "GET") {
        // GET without body support - return error with instructions
        return new Response(
          JSON.stringify({
            status: "fail",
            message:
              "GET with body not supported. Use POST or configure Nginx proxy.",
          }),
          {
            status: 400,
            headers: { "Content-Type": "application/json" },
          }
        );
      }
    }

    return new Response("Not Found", { status: 404 });
  },
});

logger.info({ url: server.url.hostname, port: server.port }, "file_api listening");
