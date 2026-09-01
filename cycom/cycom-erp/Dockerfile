# CyCom ERP frontend (Next.js 16) — standalone production image.
# Multi-stage: build the app, then ship only the self-contained standalone
# server (.next/standalone + static + public). Runtime image is small and
# low-memory — important for the 0.5 GB demo box.
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# NEXT_PUBLIC_* are baked at build time; app URL is fixed for the demo box.
ENV NEXT_TELEMETRY_DISABLED=1 \
    NODE_OPTIONS=--max-old-space-size=2048 \
    NEXT_PUBLIC_APP_URL=https://app.cy-com.com
RUN npm run build

FROM node:22-alpine AS run
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0
# Standalone output is self-contained; static + public are copied alongside.
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
