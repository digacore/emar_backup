import { db } from "../database/db";
import { pccAccessTokens } from "../drizzle/schema";
import { eq } from "drizzle-orm";
import { logger } from "./logger";

export const getPcc2LeggedToken = async (): Promise<string> => {
  const token = await db.query.pccAccessTokens.findFirst();
  const now = new Date();
  if (
    token &&
    new Date(new Date(token.createdAt!).getTime() + token.expiresIn * 1000) >
      new Date(now.getTime() + 60 * 1000)
  ) {
    const validTill = new Date(
      new Date(token.createdAt!).getTime() + token.expiresIn * 1000
    );
    logger.debug({ validTill }, "Existing token is valid");
    return token.token;
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

    if (!token) {
      await db.insert(pccAccessTokens).values({
        token: newToken,
        expiresIn: expiresIn,
        createdAt: new Date().toISOString(),
      });
    } else {
      await db
        .update(pccAccessTokens)
        .set({
          token: newToken,
          expiresIn: expiresIn,
          createdAt: new Date().toISOString(),
        })
        .where(eq(pccAccessTokens.id, token.id));
    }

    return newToken;
  } catch (error) {
    logger.error({ error }, "Error fetching PCC API token");
    throw error;
  }
};
