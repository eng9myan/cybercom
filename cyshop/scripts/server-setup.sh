#!/bin/bash
# Add cyshop.cy-com.com vhost to existing OCI nginx server (158.178.130.4)
# Run: ssh ubuntu@158.178.130.4 "bash -s" < scripts/server-setup.sh

set -e
echo "=== CyShop vhost setup on cy-com.com OCI server ==="

# 1. Create web root
sudo mkdir -p /var/www/cyshop
sudo chown -R ubuntu:ubuntu /var/www/cyshop
echo "<html><body>CyShop loading...</body></html>" > /var/www/cyshop/index.html

# 2. Install nginx vhost config
sudo tee /etc/nginx/sites-available/cyshop > /dev/null <<'NGINXCONF'
server {
    listen 80;
    server_name cyshop.cy-com.com;

    root /var/www/cyshop;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
    gzip_min_length 256;
}
NGINXCONF

# 3. Enable site (keeps all existing sites running)
sudo ln -sf /etc/nginx/sites-available/cyshop /etc/nginx/sites-enabled/cyshop

# 4. Allow passwordless nginx reload for GitHub Actions deploy
echo "ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl reload nginx" | sudo tee /etc/sudoers.d/nginx-reload > /dev/null

# 5. Test config and reload (safe — does not restart, keeps cy-com.com live)
sudo nginx -t && sudo systemctl reload nginx

echo ""
echo "=== Done ==="
echo "cyshop.cy-com.com vhost active → /var/www/cyshop"
echo "DNS: GoDaddy A record  cyshop → 158.178.130.4  TTL 600"
