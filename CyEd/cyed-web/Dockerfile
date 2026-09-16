# CyEd frontend image (Next.js). Build context = cyed-web/.
FROM node:20-slim AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund
COPY . .
RUN npm run build

FROM node:20-slim
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app ./
EXPOSE 3000
# CYED_BACKEND_URL points the proxy at the API service.
CMD ["npm", "run", "start"]
