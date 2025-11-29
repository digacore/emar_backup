import { db } from "../database/db";
import { pccAccessTokens } from "../drizzle/schema";
import { eq } from "drizzle-orm";
import { logger } from "./logger";
import { getCurrentTimestamp } from "./timestamp";

export const getPcc2LeggedToken = async (): Promise<string> => {
  const token = await db.query.pccAccessTokens.findFirst();

  logger.info(
    {
      tokenExists: !!token,
      tokenCreatedAt: token?.createdAt,
      tokenExpiresIn: token?.expiresIn,
    },
    "Checking PCC token"
  );

  if (token) {
    // Parse token.createdAt as Eastern Time string (format: "2025-11-28 16:36:13")
    // Convert to UTC by adding 5 hours (EST offset)
    const [datePart, timePart] = token.createdAt!.split(" ");
    const createdAtLocal = new Date(`${datePart}T${timePart}`);
    const createdAtUTC = new Date(
      createdAtLocal.getTime() + 5 * 60 * 60 * 1000
    ); // Add 5 hours for EST
    const expiresAt = new Date(createdAtUTC.getTime() + token.expiresIn * 1000);
    const now = new Date();
    const expiresInFuture = expiresAt > new Date(now.getTime() + 60 * 1000);

    logger.info(
      {
        createdAt: token.createdAt,
        createdAtLocal: createdAtLocal.toISOString(),
        createdAtUTC: createdAtUTC.toISOString(),
        expiresAt: expiresAt.toISOString(),
        now: now.toISOString(),
        expiresInSeconds: Math.floor(
          (expiresAt.getTime() - now.getTime()) / 1000
        ),
        isValid: expiresInFuture,
      },
      "Token validation check"
    );

    // Check if token expires more than 60 seconds from now
    if (expiresInFuture) {
      logger.info("Existing token is valid, reusing");
      return token.token;
    }
    logger.info("Token expired, fetching new one");
  }

  const serverPath = "auth/token";
  const baseUrl = process.env.PCC_BASE_URL!;
  const url = `${
    baseUrl.endsWith("/") ? baseUrl.slice(0, -1) : baseUrl
  }/${serverPath}`;

  //     base64_secret = get_base64_string(f"{CFG.PCC_CLIENT_ID}:{CFG.PCC_CLIENT_SECRET}")
  const base64Secret = btoa(
    `${process.env.PCC_CLIENT_ID}:${process.env.PCC_CLIENT_SECRET}`
  );

  logger.info({ url }, "Requesting PCC 2-legged token");
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Basic ${base64Secret}`,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        grant_type: "client_credentials",
      }),
      // Bun-specific TLS configuration for client certificates
      tls: {
        cert: await Bun.file(process.env.CERTIFICATE_PATH!).text(),
        key: await Bun.file(process.env.PRIVATEKEY_PATH!).text(),
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      logger.error(
        { status: response.status, errorText },
        "HTTP error when fetching PCC token"
      );
      throw new Error(
        `HTTP error! status: ${response.status}, body: ${errorText}`
      );
    }

    const responseData = (await response.json()) as {
      access_token: string;
      expires_in: number;
    };

    // TODO: Add proper validation schema for TwoLeggedAuthResult
    const accessTokenInfo = {
      access_token: responseData.access_token,
      expires_in: responseData.expires_in,
    };

    // Save new token to DB
    const newToken = accessTokenInfo.access_token;
    const expiresIn = accessTokenInfo.expires_in;
    const timestamp = getCurrentTimestamp();

    if (!token) {
      await db.insert(pccAccessTokens).values({
        token: newToken,
        expiresIn: expiresIn,
        createdAt: timestamp,
      });
    } else {
      await db
        .update(pccAccessTokens)
        .set({
          token: newToken,
          expiresIn: expiresIn,
          createdAt: timestamp,
        })
        .where(eq(pccAccessTokens.id, token.id));
    }

    return newToken;
  } catch (error) {
    logger.error({ error }, "Error fetching PCC API token");
    throw error;
  }
};
