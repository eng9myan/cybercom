#!/bin/bash
# ============================================================
#  CyberCom Revolution — Oracle Cloud First-Time Server Setup
#  Run ONCE after creating your OCI instance:
#  sudo bash server-setup.sh
# ============================================================
set -e

DOMAIN="cy-com.com"
WWW_DOMAIN="www.cy-com.com"
WEBROOT="/var/www/cy-com.com"
REPO="https://github.com/eng9myan/Cybercom-Website.git"
EMAIL="m.alnsour@outlook.com"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  CyberCom Revolution — Server Setup      ║"
echo "╚══════════════════════════════════════════╝"

# ── System update ─────────────────────────────────────────
echo "[1/7] Updating system..."
apt-get update -y && apt-get upgrade -y

# ── Install tools ─────────────────────────────────────────
echo "[2/7] Installing Nginx, Git, Certbot..."
apt-get install -y nginx git certbot python3-certbot-nginx \
  iptables-persistent ufw

# ── Firewall ──────────────────────────────────────────────
echo "[3/7] Opening ports 80 & 443..."
iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80  -j ACCEPT
iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
netfilter-persistent save

# ── Clone website ─────────────────────────────────────────
echo "[4/7] Cloning website from GitHub..."
rm -rf "$WEBROOT"
git clone "$REPO" "$WEBROOT"
chown -R www-data:www-data "$WEBROOT"
chmod -R 755 "$WEBROOT"

# ── Nginx config ──────────────────────────────────────────
echo "[5/7] Configuring Nginx..."
cat > /etc/nginx/sites-available/$DOMAIN << 'NGINXEOF'
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
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    gzip on;
    gzip_types text/html text/css application/javascript;
    gzip_min_length 256;

    location ~* \.(html|css|js|svg|ico|woff2?)$ {
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location ~ /.well-known/acme-challenge {
        allow all;
        root /var/www/certbot;
    }
}
NGINXEOF

ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/$DOMAIN
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl enable nginx && systemctl restart nginx
echo "  → Nginx ready ✓"

# ── SSL ───────────────────────────────────────────────────
echo "[6/7] Getting SSL certificate..."
echo ""
echo "  ⚠  Make sure DNS (cy-com.com & www.cy-com.com)"
echo "     already points to this server's IP before continuing."
echo ""
read -p "  DNS is pointing here? Press ENTER to continue..."

certbot --nginx \
  -d "$DOMAIN" -d "$WWW_DOMAIN" \
  --non-interactive --agree-tos \
  --email "$EMAIL" --redirect

# ── Auto-renewal ──────────────────────────────────────────
echo "[7/7] Enabling SSL auto-renewal..."
systemctl enable certbot.timer && systemctl start certbot.timer

# ── Allow GitHub Actions to deploy ────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  SETUP COMPLETE!                                     ║"
echo "║  Site live at: https://www.cy-com.com                ║"
echo "║                                                      ║"
echo "║  Next: add OCI_HOST and OCI_SSH_KEY to              ║"
echo "║  GitHub → Settings → Secrets → Actions              ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
