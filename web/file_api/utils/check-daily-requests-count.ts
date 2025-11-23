import { db } from "../database/db";
import { pccDailyRequests } from "../drizzle/schema";
import { gt } from "drizzle-orm";

// Get the daily quota limit from environment (convert to number)
const dailyQuotaLimit = parseInt(
  process.env.PCC_DAILY_QUOTA_LIMIT || "100",
  10
);

export const checkDailyRequestsCount = async (): Promise<Response | true> => {
  // Get the valid requests count for current time
  const currentRequestsNumber = await db.query.pccDailyRequests.findFirst({
    where: gt(pccDailyRequests.resetTime, new Date().toISOString()),
  });

  // If there is no suitable counter for current time - skip
  if (
    !currentRequestsNumber ||
    currentRequestsNumber.requestsCount < dailyQuotaLimit
  ) {
    return true;
  }

  // If requests count is exceeded - return 429 response
  if (currentRequestsNumber.requestsCount >= dailyQuotaLimit) {
    console.error(
      `Daily requests limit exceeded [${new Date().toISOString()}]. Current requests count: ${
        currentRequestsNumber.requestsCount
      }`
    );
    return new Response(
      JSON.stringify({
        error: "Daily requests limit exceeded",
        current_requests_count: currentRequestsNumber.requestsCount,
        limit: dailyQuotaLimit,
      }),
      {
        status: 429,
        headers: {
          "Content-Type": "application/json",
        },
      }
    );
  }

  return true;
};
