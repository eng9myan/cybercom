#!/usr/bin/env bash
# CyCom DEMO box — free OCI E2.1.Micro (~0.5 GB, Oracle Linux 9), NATIVE (no
# Docker, to save RAM): Django (SQLite + dev-auth) via gunicorn + a prebuilt
# Next.js standalone via node + Caddy (auto-TLS + basic-auth). Seeds a live
# café/retail Commerce demo for sales.
#
# Layout on the box:
#   ~/app        = code bundle (this script is ~/app/scripts/deploy_micro.sh)
#   ~/frontend   = extracted Next standalone (server.js + node_modules + .next)
#
# Run:  bash ~/app/scripts/deploy_micro.sh
# Prereqs (operator): DNS app.cy-com.com -> box IP (DNS-only), and OCI security
# list ingress for 22/80/443.
set -euo pipefail

APP_DOMAIN=app.cy-com.com
DEV_TENANT=11111111-1111-1111-1111-111111111111
REPO="$(cd "$(dirname "$0")/.." && pwd)"
FE="$HOME/frontend"
U="$(whoami)"; H="$HOME"

echo "==> [1/8] Swap (RAM headroom)"
if ! sudo swapon --show | grep -q /swapfile; then
  sudo fallocate -l 3G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=3072
  sudo chmod 600 /swapfile; sudo mkswap /swapfile; sudo swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

echo "==> [2/8] Packages (python3.12, node20, caddy) via dnf"
sudo dnf install -y python3.12 python3.12-devel gcc libpq-devel curl >/dev/null
if ! command -v node >/dev/null 2>&1; then
  curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash - >/dev/null
  sudo dnf install -y nodejs >/dev/null
fi
if ! command -v caddy >/dev/null 2>&1; then
  curl -fsSL "https://caddyserver.com/api/download?os=linux&arch=amd64" -o /tmp/caddy
  sudo install -m 0755 /tmp/caddy /usr/bin/caddy
  sudo useradd --system --create-home --home-dir /var/lib/caddy --shell /usr/sbin/nologin caddy 2>/dev/null || true
  sudo mkdir -p /etc/caddy
fi

# Django 6 needs SQLite >= 3.37; OL9 ships 3.34. Build a modern libsqlite3 and
# make python's stdlib sqlite3 use it via LD_LIBRARY_PATH (keeps getlimit()
# support that pysqlite3 lacks).
if ! /usr/local/bin/sqlite3 --version 2>/dev/null | grep -qE '3\.(3[7-9]|[4-9][0-9])'; then
  echo "==> [2b/8] Build modern SQLite"
  SQV=3450300
  curl -fsSL "https://www.sqlite.org/2024/sqlite-autoconf-${SQV}.tar.gz" -o /tmp/sqlite.tar.gz
  tar xzf /tmp/sqlite.tar.gz -C /tmp
  ( cd /tmp/sqlite-autoconf-${SQV} && ./configure --prefix=/usr/local >/dev/null && make -j2 >/dev/null && sudo make install >/dev/null )
  sudo ldconfig
fi
export LD_LIBRARY_PATH=/usr/local/lib

echo "==> [3/8] Backend venv + deps"
python3.12 -m venv "$H/venv"
"$H/venv/bin/pip" install --upgrade pip wheel >/dev/null
"$H/venv/bin/pip" install -r "$REPO/cycom/requirements.txt" gunicorn uvicorn >/dev/null

echo "==> [4/8] Migrate + seed café/retail demo (SQLite, dev-auth)"
export DJANGO_SETTINGS_MODULE=core.settings_dev DJANGO_DEBUG=True CYCOM_DEV_AUTH=1
export PYTHONPATH="$REPO:$REPO/cycom"
cd "$REPO/cycom"
PY="$H/venv/bin/python"
find "$REPO" -name 'cycom_dev.sqlite3' -delete 2>/dev/null || true   # clean slate
$PY manage.py migrate --noinput
$PY manage.py seed_dev_tenant || true
$PY manage.py seed_packs || true
$PY manage.py seed_demo_commerce --tenant "$DEV_TENANT" || true
$PY manage.py collectstatic --noinput || true

echo "==> [5/8] Backend service (gunicorn :8000, 1 worker)"
sudo tee /etc/systemd/system/cycom-backend.service >/dev/null <<UNIT
[Unit]
Description=CyCom backend (demo)
After=network.target
[Service]
User=$U
WorkingDirectory=$REPO/cycom
Environment=DJANGO_SETTINGS_MODULE=core.settings_dev
Environment=DJANGO_DEBUG=True
Environment=CYCOM_DEV_AUTH=1
Environment=PYTHONPATH=$REPO:$REPO/cycom
Environment=LD_LIBRARY_PATH=/usr/local/lib
ExecStart=$H/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 1 --worker-class uvicorn.workers.UvicornWorker --timeout 60 core.asgi:application
Restart=always
[Install]
WantedBy=multi-user.target
UNIT

echo "==> [6/8] Frontend service (node standalone :3000)"
sudo tee /etc/systemd/system/cycom-frontend.service >/dev/null <<UNIT
[Unit]
Description=CyCom frontend (demo)
After=network.target cycom-backend.service
[Service]
User=$U
WorkingDirectory=$FE
Environment=NODE_ENV=production
Environment=PORT=3000
Environment=HOSTNAME=127.0.0.1
Environment=CYCOM_BACKEND_URL=http://127.0.0.1:8000
Environment=CYCOM_DEV_AUTH=1
Environment=CYCOM_TENANT_ID=$DEV_TENANT
Environment=NEXT_PUBLIC_APP_URL=https://$APP_DOMAIN
ExecStart=/usr/bin/node $FE/server.js
Restart=always
[Install]
WantedBy=multi-user.target
UNIT

echo "==> [7/8] Caddy (auto-TLS)"
# No basic-auth: it blocks the SPA's client-side XHR (browsers don't resend
# basic-auth creds on fetch), breaking KDS/live pages. The demo is fake data
# behind dev-auth auto-login, so an open URL is what sales wants anyway.
sudo tee /etc/caddy/Caddyfile >/dev/null <<CADDY
{
	email admin@cy-com.com
}
$APP_DOMAIN {
	reverse_proxy 127.0.0.1:3000
}
CADDY
sudo tee /etc/systemd/system/caddy.service >/dev/null <<UNIT
[Unit]
Description=Caddy
After=network.target
[Service]
User=caddy
Group=caddy
Environment=XDG_DATA_HOME=/var/lib/caddy
Environment=XDG_CONFIG_HOME=/etc/caddy
ExecStart=/usr/bin/caddy run --config /etc/caddy/Caddyfile
ExecReload=/usr/bin/caddy reload --config /etc/caddy/Caddyfile
Restart=always
AmbientCapabilities=CAP_NET_BIND_SERVICE
[Install]
WantedBy=multi-user.target
UNIT

echo "==> [8/8] Firewall 80/443 + start services"
if command -v firewall-cmd >/dev/null 2>&1 && sudo systemctl is-active --quiet firewalld; then
  sudo firewall-cmd --permanent --add-service=http --add-service=https || true
  sudo firewall-cmd --reload || true
fi
if command -v iptables >/dev/null 2>&1; then
  sudo iptables -C INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null || sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT || true
  sudo iptables -C INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null || sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT || true
fi
sudo systemctl daemon-reload
sudo systemctl enable --now cycom-backend cycom-frontend caddy
sleep 6
echo
echo "############################################################"
echo "CyCom DEMO is live:  https://$APP_DOMAIN  (open URL, dev-auth auto-login)"
echo "  Demo tenant: café/retail Commerce (catalog + POS + KDS + quotations)"
echo "  Dev-auth ON (demo only). Full signup/pay = the A1 box, later."
echo "  (Caddy issues TLS once DNS $APP_DOMAIN -> this box resolves.)"
echo "############################################################"
systemctl --no-pager --lines=3 status cycom-backend cycom-frontend caddy 2>/dev/null | grep -E 'cycom|caddy|Active:' || true
