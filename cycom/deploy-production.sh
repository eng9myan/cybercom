#!/usr/bin/env bash
# ============================================================
#  CyCom ERP Frontend — Production Deployment Script
#  Run this script on the production server to deploy the ERP UI.
#  Runs the Next.js app on port 3005 via PM2.
# ============================================================
set -e

APP_DIR="/opt/cycom-erp"
REPO="https://github.com/eng9myan/CyCom.git"

echo "▶ Preparing CyCom ERP directory..."
if [ -d "$APP_DIR/.git" ]; then
  cd "$APP_DIR"
  git pull origin main
else
  sudo mkdir -p "$APP_DIR"
  sudo chown -R ubuntu:ubuntu "$APP_DIR"
  git clone "$REPO" "$APP_DIR"
  cd "$APP_DIR"
fi

# Enter Next.js app directory
cd cycom-erp

# Copy environment file if not exists
if [ ! -f .env.local ]; then
  echo "▶ Creating production env file..."
  cat > .env.local << 'ENVEOF'
CYCOM_BACKEND_URL=http://localhost:8069
CYCOM_DB=cycom
ENVEOF
fi

echo "▶ Installing dependencies..."
npm install

echo "▶ Building Next.js application..."
npm run build

echo "▶ Starting CyCom ERP via PM2 on port 3005..."
if ! command -v pm2 &> /dev/null; then
  sudo npm install -g pm2
fi

# Start or reload the process
pm2 start "npm run start -- -p 3005" --name "cycom-erp" || pm2 reload "cycom-erp"

echo "✅ CyCom ERP Frontend deployed successfully on port 3005!"
