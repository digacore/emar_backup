import type { HeadersInit } from "bun";
import { checkDailyRequestsCount } from "./check-daily-requests-count";

export const executePccRequest = async (
  url: string,
  headers: HeadersInit,
  method: string = "GET",
  body?: any
) => {
  // Check daily requests count and raise error if it's exceeded
  const checkResult = await checkDailyRequestsCount();
  if (checkResult instanceof Response) {
    return checkResult;
  }

  try {
    const response = await fetch(url, {
      method,
      headers,
      body: JSON.stringify(body),
      // Bun-specific TLS configuration for client certificates
      tls: {
        cert: await Bun.file(process.env.CERTIFICATE_PATH!).text(),
        key: await Bun.file(process.env.PRIVATEKEY_PATH!).text(),
      },
    });

    if (!response.ok) {
      console.error(
        `Failed to execute PCC request. Status: ${response.status}, StatusText: ${response.statusText}`
      );
      throw new Error(`PCC request failed with status ${response.status}`);
    }

    return response;
  } catch (error) {
    console.error("Error executing PCC request:", error);
    return new Response("Error executing PCC request", { status: 500 });
  }
};
