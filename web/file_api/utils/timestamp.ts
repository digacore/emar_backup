/**
 * Get current timestamp in America/New_York timezone
 * formatted as YYYY-MM-DD HH:MM:SS
 */
export const getCurrentTimestamp = (): string => {
  return new Date()
    .toLocaleString("en-US", {
      timeZone: "America/New_York",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    })
    .replace(/(\d+)\/(\d+)\/(\d+),\s+(\d+):(\d+):(\d+)/, "$3-$1-$2 $4:$5:$6");
};
