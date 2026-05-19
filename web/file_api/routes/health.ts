import { pool } from "../database/db";

export const healthCheck = async (): Promise<Response> => {
  try {
    await pool.query("SELECT 1");
    return Response.json({
      status: "ok",
      service: "file_api",
      database: "connected",
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return Response.json(
      {
        status: "error",
        service: "file_api",
        database: "disconnected",
        error: message,
      },
      { status: 503 }
    );
  }
};
