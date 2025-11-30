import pino from "pino";

const usePrettyLogs = process.env.USE_PRETTY_LOGS !== "false";

export const logger = pino({
  level: "info",
  transport: {
    target: "pino-pretty",
    options: {
      colorize: true,
      translateTime: "UTC:yyyy-mm-dd HH:MM:ss.l +0000", // Force UTC like Flask
      ignore: "pid,hostname",
    },
  },
  formatters: {
    level: (label) => {
      return { level: label };
    },
  },
});
