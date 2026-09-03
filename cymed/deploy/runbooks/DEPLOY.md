# CyMed — First-deploy checklist

Use this the first time you cut CyMed onto a fresh AWS account + EKS cluster.
Every line is a checkbox — copy the whole block into a ticket and sign off as
you go.

---

## 0. Prerequisites (do once per account)

- [ ] AWS account provisioned; guardrails via Control Tower / Landing Zone applied
- [ ] Route53 hosted zone for `cymed.example.com` exists and delegation is live
- [ ] ACM certificate requested for `*.cymed.example.com` in the target region
- [ ] Terraform remote state bootstrapped (see `deploy/terraform/aws/README.md`)
- [ ] OIDC federation for GitHub Actions -> AWS role (`arn:aws:iam::<acct>:role/gha-cymed-deployer`)
- [ ] Secrets Manager entries created for: `cymed/prod/db_password`, `cymed/prod/django_secret_key`
- [ ] KMS keys documented in the security register

## 1. Provision infrastructure (Terraform)

- [ ] `terraform workspace select prod`
- [ ] `TF_VAR_db_password=$(aws secretsmanager get-secret-value --secret-id cymed/prod/db_password --query SecretString --output text) terraform plan -var-file=envs/prod.tfvars -out=plan.tfplan`
- [ ] Review plan diff with a second engineer
- [ ] `terraform apply plan.tfplan`
- [ ] Capture outputs: `terraform output > /tmp/tfout.json`
- [ ] Verify RDS is Multi-AZ, deletion protection ON, backup retention 30 days
- [ ] Verify ElastiCache Redis has TLS in transit + at-rest encryption
- [ ] Verify S3 artefacts bucket blocks public access + SSE-KMS

## 2. Cluster bootstrap

- [ ] `aws eks update-kubeconfig --name cymed-prod --alias cymed-prod`
- [ ] `kubectl get nodes` — all three nodes Ready across three AZs
- [ ] Install ingress-nginx (see `deploy/k8s/README.md`)
- [ ] Install cert-manager + apply `letsencrypt-prod` ClusterIssuer
- [ ] Install sealed-secrets controller
- [ ] Install metrics-server (needed by HPA)
- [ ] Optional: install `kube-prometheus-stack` in namespace `observability`

## 3. Secrets

- [ ] Fill `deploy/k8s/base/secret.env.yaml` locally (do not commit)
- [ ] `kubeseal --format=yaml < secret.env.yaml > deploy/k8s/overlays/prod/sealed-secret.env.yaml`
- [ ] Commit `sealed-secret.env.yaml` (safe — it's asymmetrically encrypted)
- [ ] Verify: `kubectl -n cymed get sealedsecret cymed-secrets`

## 4. First image build

- [ ] Push to `main` — the `build-and-push` workflow builds and tags
      `ghcr.io/cybercom/cymed-{api,worker,beat}:sha-<git-sha>` and `:latest`
- [ ] `cosign verify` the images (see `deploy/k8s/README.md`)
- [ ] Pin the overlay to the SHA: edit
      `deploy/k8s/overlays/prod/kustomization.yaml` `images:` block

## 5. Apply the workload

- [ ] `kubectl kustomize deploy/k8s/overlays/prod | kubectl diff -f -`
- [ ] Review diff with a second engineer
- [ ] `kubectl apply -k deploy/k8s/overlays/prod`
- [ ] `kubectl -n cymed rollout status deploy/cymed-api --timeout=5m`
- [ ] `kubectl -n cymed rollout status deploy/cymed-worker --timeout=5m`
- [ ] `kubectl -n cymed rollout status deploy/cymed-beat --timeout=2m`

## 6. Database bootstrap

- [ ] Run migrations as a one-off Job (or exec into an API pod):
      `kubectl -n cymed exec -it deploy/cymed-api -- python manage.py migrate`
- [ ] Create the initial superuser via `manage.py createsuperuser` or a
      management command that pulls from Secrets Manager
- [ ] Seed baseline data (Ready-ERP templates, country packs) via
      `python manage.py loaddata <fixture>` or the platform provisioning API

## 7. Post-deploy verification

- [ ] `curl -f https://api.cymed.example.com/health` returns 200
- [ ] `curl -f https://api.cymed.example.com/health/liveness` returns 200
- [ ] `curl -f https://api.cymed.example.com/metrics` returns Prometheus text
- [ ] Ingress TLS cert issued by Let's Encrypt (browser green padlock)
- [ ] HPA target CPU shows 0-5% at rest: `kubectl -n cymed get hpa`
- [ ] Sample workflow end-to-end: patient create -> encounter -> claim
- [ ] Celery task fires: dispatch a test task, confirm it runs on a worker
- [ ] Beat schedule fires: confirm a scheduled task ran once in the log
- [ ] Sentry (or equivalent) receives a test event
- [ ] OpenTelemetry traces visible in the collector

## 8. Sign-off

- [ ] Runbook links (INCIDENT, DR, BACKUP, ROLLBACK) posted in on-call channel
- [ ] Monitors and alerts armed
- [ ] Change log entry filed
- [ ] Announcement to stakeholders sent
