# syntax=docker/dockerfile:1.7
FROM node:20-alpine AS builder

WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

COPY . .
RUN npm ci

# Build Web application
RUN --mount=type=secret,id=production_env,target=/app/apps/web/.env.production,required=false \
    npm run build --workspace=@cybercom/web

# Build Portal, Partners, and Docs applications
RUN npm run build --workspace=@cybercom/portal
RUN npm run build --workspace=@cybercom/partners
RUN npm run build --workspace=@cybercom/docs

FROM node:20-alpine AS runner

WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0

RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

# Copy Web standalone (port 3000)
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/static ./apps/web/.next/static

# Copy Portal standalone (port 3001)
COPY --from=builder --chown=nextjs:nodejs /app/apps/portal/.next/standalone ./apps/portal-standalone
COPY --from=builder --chown=nextjs:nodejs /app/apps/portal/.next/static ./apps/portal-standalone/apps/portal/.next/static

# Copy Partners standalone (port 3002)
COPY --from=builder --chown=nextjs:nodejs /app/apps/partners/.next/standalone ./apps/partners-standalone
COPY --from=builder --chown=nextjs:nodejs /app/apps/partners/.next/static ./apps/partners-standalone/apps/partners/.next/static

# Copy Docs standalone (port 3003)
COPY --from=builder --chown=nextjs:nodejs /app/apps/docs/.next/standalone ./apps/docs-standalone
COPY --from=builder --chown=nextjs:nodejs /app/apps/docs/.next/static ./apps/docs-standalone/apps/docs/.next/static

# Startup script to run all Next.js servers concurrently
RUN printf '#!/bin/sh\n\
PORT=3000 node apps/web/server.js &\n\
PORT=3001 node apps/portal-standalone/apps/portal/server.js &\n\
PORT=3002 node apps/partners-standalone/apps/partners/server.js &\n\
PORT=3003 node apps/docs-standalone/apps/docs/server.js &\n\
wait\n' > /app/start.sh \
    && chmod +x /app/start.sh \
    && chown nextjs:nodejs /app/start.sh

USER nextjs
EXPOSE 3000 3001 3002 3003

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD wget -qO- http://127.0.0.1:3000/api/health >/dev/null || exit 1

CMD ["/app/start.sh"]
