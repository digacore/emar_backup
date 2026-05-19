# Bun 1.2.3+ required for Bun.serve routes API (see index.ts)
FROM oven/bun:1.2.3 AS base
WORKDIR /usr/src/app
COPY package.json bun.lock* ./
RUN bun install --production
COPY . .

EXPOSE 3000/tcp
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD bun -e "fetch('http://127.0.0.1:3000/health').then((r)=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"
ENTRYPOINT [ "bun", "run", "index.ts" ]