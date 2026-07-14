#!/bin/bash
# ============================================================
#  CyberCom Revolution — EC2 Deployment Script
#  Domain : www.cy-com.com
#  Server : Ubuntu + Nginx
#  Run as : sudo bash deploy.sh
# ============================================================

set -e

DOMAIN="cy-com.com"
WWW_DOMAIN="www.cy-com.com"
WEBROOT="/var/www/cy-com.com"
REPO="https://github.com/eng9myan/Cybercom-Website.git"
NGINX_CONF="/etc/nginx/sites-available/$DOMAIN"
EMAIL="m.alnsour@outlook.com"   # used for Let's Encrypt notifications

echo ""
echo "=================================================="
echo "  CyberCom Revolution — Deployment Starting"
echo "=================================================="
echo ""

# ── 1. Update system & install dependencies ──────────────
echo "[1/6] Updating system packages..."
apt-get update -y && apt-get upgrade -y

echo "[1/6] Installing Nginx, Git, Certbot..."
apt-get install -y nginx git certbot python3-certbot-nginx

# ── 2. Clone / pull website from GitHub ──────────────────
echo ""
echo "[2/6] Deploying website files from GitHub..."
if [ -d "$WEBROOT/.git" ]; then
    echo "  → Repo exists, pulling latest..."
    git -C "$WEBROOT" pull origin main
else
    echo "  → Cloning repo into $WEBROOT..."
    rm -rf "$WEBROOT"
    git clone "$REPO" "$WEBROOT"
fi

chown -R www-data:www-data "$WEBROOT"
chmod -R 755 "$WEBROOT"

# ── 3. Install Nginx config ───────────────────────────────
echo ""
echo "[3/6] Configuring Nginx..."
cat > "$NGINX_CONF" << 'NGINXEOF'
server {
    listen 80;
    listen [::]:80;
    server_name cy-com.com;
    return 301 https://www.cy-com.com$request_uri;
}

server {
    listen 80;
    listen [::]:80;
    server_name www.cy-com.com;

    root /var/www/cy-com.com;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    gzip on;
    gzip_types text/html text/css application/javascript text/javascript;
    gzip_min_length 256;

    location ~* \.(html|css|js|jpg|jpeg|png|gif|svg|ico|woff2?)$ {
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location ~ /.well-known/acme-challenge {
        allow all;
        root /var/www/certbot;
    }
}
NGINXEOF

# Enable the site
if [ ! -L /etc/nginx/sites-enabled/$DOMAIN ]; then
    ln -s "$NGINX_CONF" /etc/nginx/sites-enabled/$DOMAIN
fi

# Remove default site if it exists
rm -f /etc/nginx/sites-enabled/default

# Test and reload Nginx
nginx -t && systemctl reload nginx
echo "  → Nginx configured and reloaded ✓"

# ── 4. Open firewall ──────────────────────────────────────
echo ""
echo "[4/6] Configuring UFW firewall..."
ufw allow 'Nginx Full' 2>/dev/null || true
ufw allow OpenSSH 2>/dev/null || true
echo "  → Ports 80 & 443 open ✓"

# ── 5. SSL Certificate via Let's Encrypt ─────────────────
echo ""
echo "[5/6] Obtaining SSL certificate (Let's Encrypt)..."
echo "  ⚠  DNS must already point to this server's IP before this step."
echo ""

certbot --nginx \
  -d "$DOMAIN" \
  -d "$WWW_DOMAIN" \
  --non-interactive \
  --agree-tos \
  --email "$EMAIL" \
  --redirect

echo "  → SSL certificate installed ✓"

# ── 6. Enable auto-renewal ───────────────────────────────
echo ""
echo "[6/6] Setting up auto-renewal..."
systemctl enable certbot.timer
systemctl start certbot.timer
echo "  → Auto-renewal enabled ✓"

echo ""
echo "=================================================="
echo "  DONE! Your site is live at:"
echo "  https://www.cy-com.com"
echo "=================================================="
echo ""
