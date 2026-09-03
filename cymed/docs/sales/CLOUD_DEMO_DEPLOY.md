# CyMed Always-On Cloud Demo — devops runbook

**Version:** 1.0
**Date:** 2026-08-26
**Owner:** Cybercom devops
**Goal:** stand up a public demo at `demo.cymed.io` so the sales team gets a stable URL to hand out — no laptop dependency.

**Cost:** ~US $18–25/month all-in (VPS + domain + certificates + monitoring).

---

## 1. Domain + DNS

**Recommended:** register `cymed.health` (credibility) with a `demo.` subdomain. Fallback: `cymed.io`.

- Registrar: Cloudflare (bundles DNS + free CDN + free basic WAF)
- DNS: A record `demo.cymed.health` → VPS IPv4
- TTL: 300s during setup, 3600s once stable

Optional: `www.cymed.health` → same IP for the marketing site (later).

---

## 2. VPS choice

| Provider | Plan | Cost | Notes |
|---|---|---|---|
| **Hetzner CX22** | 2 vCPU · 4 GB · 40 GB SSD · Nuremberg / Falkenstein / Helsinki | €5.83/mo | Best price:perf; EU data-residency |
| **DigitalOcean Basic** | 2 vCPU · 4 GB · 80 GB SSD · Frankfurt | $18/mo | Simpler dashboard; managed backups add $2 |
| **AWS Lightsail** | 2 vCPU · 4 GB · 80 GB SSD · Bahrain (me-south-1) | $20/mo | Middle-East residency claim |
| **Petra Hosting** (JO local) | dedicated JO datacenter | ~$30/mo | Data-residency selling point for JO prospects |

**Pick Petra or AWS Bahrain if data residency in the pitch matters.** Otherwise Hetzner wins on cost.

---

## 3. Base image

Ubuntu 24.04 LTS. Create a non-root user `cymed` with sudo.

```bash
# on first login as root
adduser cymed
usermod -aG sudo cymed
rsync --archive --chown=cymed:cymed ~/.ssh /home/cymed
sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
systemctl restart ssh
```

Log out. Continue as `cymed`.

---

## 4. Bring-up — 20 idempotent commands

```bash
# 1. Base packages
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl ca-certificates gnupg ufw

# 2. Firewall
sudo ufw allow 22/tcp && sudo ufw allow 80/tcp && sudo ufw allow 443/tcp
sudo ufw --force enable

# 3. Docker + compose
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker cymed
newgrp docker

# 4. Clone repo
cd /opt && sudo git clone https://github.com/cybercom/cymed.git
sudo chown -R cymed:cymed cymed
cd cymed

# 5. Env
cp .env.example .env
# edit .env — set DJANGO_SECRET_KEY (openssl rand -hex 32), DB_PASSWORD, ALLOWED_HOSTS=demo.cymed.health
${EDITOR:-nano} .env

# 6. Bring up the demo stack
docker compose -f deploy/docker/docker-compose.prod-like.yml up -d

# 7. Wait for Postgres
until docker compose -f deploy/docker/docker-compose.prod-like.yml exec -T postgres pg_isready -U cymed; do sleep 2; done

# 8. Migrate + seed
docker compose -f deploy/docker/docker-compose.prod-like.yml exec -T api python manage.py migrate
docker compose -f deploy/docker/docker-compose.prod-like.yml exec -T api python manage.py seed_specialized_hospital --wipe --patient-count=200 --encounter-count=300

# 9. Sanity
curl -s -H "X-Tenant-ID: 4403df62-d91e-4f7a-8b26-a46118154bf4" http://127.0.0.1:8000/api/schema/ | head -c 200
```

---

## 5. Nginx + Let's Encrypt

```bash
# 10. Install nginx + certbot
sudo apt install -y nginx certbot python3-certbot-nginx

# 11. Nginx server block
sudo tee /etc/nginx/sites-available/cymed-demo <<'NGINX'
server {
    listen 80;
    server_name demo.cymed.health;

    location /static/ {
        alias /opt/cymed/staticfiles/;
        expires 30d;
    }
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Request-Id $request_id;
        proxy_read_timeout 60s;
    }
    location /demo/ {
        alias /opt/cymed/tools/demo/;
        autoindex off;
    }
    location = /admin {
        auth_basic "Restricted";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://127.0.0.1:8000/admin;
    }
    client_max_body_size 20M;
    gzip on;
    gzip_types text/plain application/json application/javascript text/css text/xml application/xml image/svg+xml;
}
NGINX

# 12. Basic-auth on /admin
sudo apt install -y apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd cymed_admin

# 13. Enable + test + reload
sudo ln -sf /etc/nginx/sites-available/cymed-demo /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# 14. TLS certificate
sudo certbot --nginx -d demo.cymed.health --non-interactive --agree-tos -m ops@cybercom.health --redirect

# 15. Auto-renew (systemd timer installed by certbot)
sudo systemctl status certbot.timer
```

---

## 6. Auto-reseed cron — nightly clean demo

```bash
# 16. Reset the demo tenant every night at 03:00 Amman time (UTC+3 -> 00:00 UTC)
sudo tee /etc/cron.d/cymed-reseed <<'CRON'
0 0 * * * cymed cd /opt/cymed && /usr/bin/docker compose -f deploy/docker/docker-compose.prod-like.yml exec -T api python manage.py seed_specialized_hospital --wipe --patient-count=200 --encounter-count=300 >> /var/log/cymed-reseed.log 2>&1
CRON
sudo touch /var/log/cymed-reseed.log && sudo chown cymed:cymed /var/log/cymed-reseed.log
```

---

## 7. Read-only demo credentials

Publish these on the demo landing page:

```
Demo tenant ID:  4403df62-d91e-4f7a-8b26-a46118154bf4
Demo doctor:     dr.demo@cymed.health / DemoDoctor2026!
Demo patient:    rania.haddad@cymed.health / DemoPatient2026!
Demo admin:      client.admin@cymed.health / DemoAdmin2026!
```

Create via a one-off command:
```bash
# 17. Seed demo user accounts
docker compose -f deploy/docker/docker-compose.prod-like.yml exec -T api python manage.py createdemousers --password-defaults
```

*(If `createdemousers` command doesn't exist yet, use Django admin at `/admin/` behind basic-auth to create them manually the first time.)*

---

## 8. Monitoring

```bash
# 18. UptimeRobot HTTP monitor on https://demo.cymed.health/health
# free tier: 50 monitors, 5-min interval; add via https://uptimerobot.com

# 19. Sentry error tracking (optional)
# free tier: 5,000 errors/month
# add SENTRY_DSN to .env and restart api container
```

---

## 9. Backup

**Not needed.** Demo data is regenerated nightly. If you want to preserve a specific state:

```bash
docker compose -f deploy/docker/docker-compose.prod-like.yml exec -T postgres \
    pg_dump -U cymed cymed_dev > backup-$(date +%F).sql
```

---

## 10. Cost estimate

| Item | Cost/mo |
|---|---|
| Hetzner CX22 (or AWS Lightsail Bahrain) | $6 – $20 |
| Domain (`cymed.health`, per year / 12) | $2 |
| Cloudflare DNS + basic WAF | $0 |
| Let's Encrypt TLS | $0 |
| UptimeRobot free tier | $0 |
| Sentry free tier | $0 |
| **Total** | **$8 – $22 / month** |

---

## 11. Security notes

- **No real patient data.** Demo tenant only. Anyone hitting `/api/v1/*` sees only synthetic data.
- **Basic auth on `/admin`** prevents accidental configuration changes by curious visitors.
- **Rate-limiting** — enable nginx `limit_req` module for `/api/` to prevent scraping:
  ```
  limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;
  location /api/ { limit_req zone=api burst=60 nodelay; ... }
  ```
- **Cloudflare** in front — automatic DDoS mitigation, hides origin IP.
- **No SSH from public internet** — restrict SSH to your office IP:
  ```bash
  sudo ufw delete allow 22/tcp
  sudo ufw allow from YOUR_OFFICE_IP to any port 22
  ```
- **Rotate Django SECRET_KEY** if you suspect compromise.

---

## 12. Kill switch

Take demo offline in 10 seconds:

```bash
# 20. Kill switch
cd /opt/cymed && docker compose -f deploy/docker/docker-compose.prod-like.yml down
sudo systemctl stop nginx
```

Bring back:
```bash
sudo systemctl start nginx
cd /opt/cymed && docker compose -f deploy/docker/docker-compose.prod-like.yml up -d
```

---

## What sales team gets after this runs

- **Stable URL:** `https://demo.cymed.health` — reachable from any browser, always fresh
- **API docs:** `https://demo.cymed.health/api/docs/`
- **Static demo shell:** `https://demo.cymed.health/demo/demo_portal.html`
- **Sample credentials** in the sales kit — client can log in and click around
- **Nightly reset** — no risk of stale demo state
- **99.9% uptime** target (VPS SLA + monitored)

Update the elevator pitch, one-pager, and email templates to point at `demo.cymed.health` instead of the artifact URL once this is live.
