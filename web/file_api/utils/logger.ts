import pino from "pino";

/** Pretty logs use a worker thread and often crash in Docker; off by default in production. */
const usePrettyLogs =
  process.env.USE_PRETTY_LOGS === "true" ||
  (process.env.NODE_ENV !== "production" &&
    process.env.USE_PRETTY_LOGS !== "false");

export const logger = usePrettyLogs
  ? pino({
      level: process.env.LOG_LEVEL ?? "info",
      transport: {
        target: "pino-pretty",
        options: {
          colorize: true,
          translateTime: "UTC:yyyy-mm-dd HH:MM:ss.l +0000",
          ignore: "pid,hostname",
        },
      },
    })
  : pino({
      level: process.env.LOG_LEVEL ?? "info",
      formatters: {
        level: (label) => ({ level: label }),
      },
    });
