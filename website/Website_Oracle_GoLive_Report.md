# CyberCom Website — Oracle Cloud Go-Live Report

Date: 2026-06-29

Target branch: `develop`

Domains: `www.cy-com.com`, `cy-com.com`

## Executive status

**BLOCKED**

The production Next.js website is live on the existing Oracle VM with a healthy Docker container, Nginx reverse proxy, canonical apex redirect, and valid combined TLS certificate. The GitHub Actions deployment is repeatable and all six repository secrets are configured. Final production acceptance remains blocked because `api.cy-com.com` has expired TLS and no CyberCom API virtual host or backend listener was found on the VM.

## Repository assessment

- Framework: Next.js App Router 16.2.9, React 19, TypeScript, `next-intl`.
- Repository structure: npm workspaces managed with Turborepo.
- Package manager: npm 10; lockfile is `package-lock.json`.
- Install: `npm ci`.
- Website build: `npm run build --workspace=@cybercom/web`.
- Website start: standalone Node server at `apps/web/server.js` inside the production image.
- Production port: container port 3000, published only on `127.0.0.1:3000`.
- Deployment: Docker on the existing ARM64 Oracle VM, behind host Nginx.
- Existing workflow issue: the previous workflow deployed the legacy static root from `main`, hardcoded `ubuntu`, and used the obsolete `OCI_SSH_KEY` secret.

## Deployment architecture

1. A push to `develop` triggers GitHub Actions.
2. CI installs locked dependencies and runs website lint, monorepo typecheck, website tests, and the production website build.
3. CI creates an archive for the exact Git commit and transfers it plus the protected production environment file over SSH.
4. The Oracle VM builds a release-tagged ARM64 Docker image using BuildKit. The production environment file is mounted as a build secret and is not copied into an image layer.
5. Docker Compose runs `cybercom-website:<git-sha>` on `127.0.0.1:3000` with an application health check.
6. Nginx terminates TLS, proxies `www.cy-com.com` to the container, and permanently redirects `cy-com.com` to `https://www.cy-com.com`.
7. The previous release image and release directory remain available for rollback.

## Oracle VM inventory

- Host: `158.178.130.4`
- OS: Ubuntu 22.04, Oracle Linux kernel, ARM64
- SSH user: `ubuntu`
- Nginx: 1.18.0, active
- Node.js: 20.20.2
- npm: 10.8.2
- Docker: 29.1.3
- PM2: installed but not used by this deployment
- Root filesystem: approximately 36 GB free during inspection
- Existing `/var/www/cy-com.com` checkout is on `main` with local modifications. It is deliberately preserved and is not used or reset by the new release deployment.

## GitHub Actions workflow

Workflow: `.github/workflows/deploy.yml`

- Trigger: push to `develop` or manual dispatch.
- Concurrency: one production deployment at a time; active deployments are not cancelled.
- Validation: install, web lint, monorepo typecheck, 16 web tests, production web build.
- Deployment transport: native SSH/SCP using the exact Git commit archive.
- Server release root: `/opt/cybercom-website/releases/<git-sha>`.
- Shared protected environment: `/opt/cybercom-website/shared/.env.production`, mode `0600`.
- Automatic rollback: if container startup, health check, or Nginx validation fails, the previous image is restarted.

## Required GitHub secrets

| Secret | Production value or purpose |
|---|---|
| `OCI_HOST` | Oracle VM public host; currently `158.178.130.4` |
| `OCI_SSH_USER` | Existing SSH account; currently `ubuntu` |
| `OCI_SSH_PRIVATE_KEY` | Private key matching the authorized VM deployment key; never commit it |
| `PRODUCTION_ENV_FILE` | Multiline dotenv content for production; never commit it |
| `NEXT_PUBLIC_API_URL` | Public API origin; expected `https://api.cy-com.com` |
| `NEXT_PUBLIC_SITE_URL` | Canonical site origin; must be `https://www.cy-com.com` |

OCI tenancy, user, fingerprint, registry, compartment, and cluster secrets are not required because this deployment uses the existing VM and does not use OCI CLI, OCIR, or OKE.

## Production environment variables

The committed `.env.production.example` documents all supported public variables. The required production variables are:

```dotenv
NEXT_PUBLIC_API_URL=https://api.cy-com.com
NEXT_PUBLIC_SITE_URL=https://www.cy-com.com
```

Optional public destinations include portal, health, provider, docs, hospital, clinic, laboratory, imaging, and pharmacy URLs. Public `NEXT_PUBLIC_*` values are intentionally visible in the browser bundle. Any server-only secret must be stored only in `PRODUCTION_ENV_FILE` or the VM's protected shared environment file.

## DNS records

Authoritative DNS is currently GoDaddy (`ns63.domaincontrol.com`, `ns64.domaincontrol.com`). The following records were resolved during inspection:

| Name | Type | Value | Status |
|---|---|---|---|
| `cy-com.com` | A | `158.178.130.4` | Present |
| `www.cy-com.com` | A | `158.178.130.4` | Present |

No DNS change is required for the website go-live unless the records are later moved or proxied through another provider.

## SSL setup

Nginx and Certbot manage TLS on the VM. The certificate named `www.cy-com.com` was expanded successfully and now contains both `www.cy-com.com` and `cy-com.com`. It is valid through 2026-09-26 and renews automatically. The one-time command used was:

```bash
sudo certbot --nginx \
  --cert-name www.cy-com.com \
  -d www.cy-com.com \
  -d cy-com.com \
  --expand \
  --non-interactive \
  --agree-tos
sudo nginx -t
sudo systemctl reload nginx
```

The Certbot renewal timer is enabled and active. After expansion, both HTTP hostnames and apex HTTPS redirect to `https://www.cy-com.com$request_uri`.

## Deployment commands

Normal deployment is automatic after a successful push to `develop`. A release on the VM is activated by:

```bash
cd /opt/cybercom-website/releases/<git-sha>
chmod +x scripts/*.sh
./scripts/deploy-production.sh <git-sha>
```

Useful verification commands:

```bash
docker ps --filter name=cybercom-website
docker logs --tail 200 cybercom-website
curl --fail http://127.0.0.1:3000/api/health
sudo nginx -t
```

## Rollback

Roll back to the previously recorded healthy release:

```bash
/opt/cybercom-website/releases/$(cat /opt/cybercom-website/current-release)/scripts/rollback-production.sh
```

Or select a retained commit explicitly:

```bash
/opt/cybercom-website/releases/<current-sha>/scripts/rollback-production.sh <target-sha>
```

The rollback script verifies that both the target release files and Docker image exist, restarts that image, and requires the internal health endpoint to pass.

## Validation results

- `npm ci`: passed.
- Website ESLint: passed with zero errors; 19 pre-existing warnings remain.
- Monorepo TypeScript check: passed.
- Website tests: 16 passed.
- Website production standalone build: passed; 121 static pages generated.
- Local standalone start: passed.
- `/api/health`: HTTP 200.
- `/robots.txt`: HTTP 200.
- `/sitemap.xml`: HTTP 200.
- `/en`: HTTP 200.
- `/en/products`: HTTP 200.
- `/en/products/cymed`: HTTP 200.
- `api.cy-com.com`: blocked by expired TLS; no CyberCom API Nginx virtual host or backend listener was found on the inspected VM.
- Docker Compose configuration: valid using the documented example environment.
- Deployment shell syntax and Git whitespace checks: passed.
- Secret scan: no private key material or obvious committed credentials found. Only environment examples are tracked.
- Dependency audit: no high or critical findings. Two moderate PostCSS findings remain inside the latest stable Next.js package; npm currently offers no safe stable upgrade and proposes an invalid downgrade.

## SEO essentials

- Global and page-specific metadata: present.
- Canonical production origin: controlled by `NEXT_PUBLIC_SITE_URL`.
- Localized canonical and alternate links: present.
- `robots.txt`: generated by Next.js.
- `sitemap.xml`: generated for English and Arabic primary routes.
- Open Graph and Twitter metadata: present.

## Final go-live checklist

- [x] Existing Oracle VM confirmed; no Oracle resources created.
- [x] Both DNS A records point to the Oracle VM.
- [x] Repeatable Docker release deployment prepared.
- [x] Nginx reverse proxy and canonical redirect prepared.
- [x] Health endpoint added.
- [x] Sitemap, robots, and metadata verified.
- [x] Rollback procedure implemented.
- [x] No committed secret or private key detected.
- [x] All six required GitHub secrets configured and name-verified without exposing values.
- [x] Conventional Commits pushed to `develop`.
- [x] GitHub Actions validation and first Docker deployment completed successfully.
- [x] Certificate expanded to include `cy-com.com`.
- [x] Public redirects, certificate SANs, main pages, product pages, health endpoint, and startup logs verified.
- [ ] Restore and verify production API calls.
- [ ] Provide or restore the real production CyberCom API endpoint and valid TLS certificate.

## Remaining blockers

1. `api.cy-com.com` resolves to `158.178.130.4`, but that VM has no `api.cy-com.com` Nginx site and no CyberCom API backend on the expected local ports. The existing services on ports 13000/18000 belong to CyShop and must not be reused by assumption. The correct production API backend or upstream URL is required.
2. The latest stable Next.js package retains two moderate PostCSS audit findings with no safe stable upgrade currently offered. There are no high or critical findings.
