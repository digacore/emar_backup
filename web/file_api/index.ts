import "dotenv/config";
import { downloadFromPCC } from "./routes/download-from-pcc.ts";
import { getCredentials } from "./routes/get-credentials.ts";
import { lastTime } from "./routes/last-time.ts";
import { getTelemetryInfo, printerInfo } from "./routes/get-telemetry.ts";

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
    "/get_telemetry_info": (req) => {
      if (req.method === "GET") {
        return getTelemetryInfo(req);
      } else {
        return new Response("Method Not Allowed", { status: 405 });
      }
    },
    "/printer_info": (req) => {
      if (req.method === "POST") {
        return printerInfo(req);
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
