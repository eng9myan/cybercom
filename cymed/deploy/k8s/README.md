# CyMed on Kubernetes

Base + overlay layout using Kustomize. Cluster prerequisites are listed at the
bottom — install those once per cluster, then apply an overlay per environment.

## Layout

```
deploy/k8s/
  base/                        <- shared spec, apply nothing here directly
    namespace.yaml
    configmap.env.yaml
    secret.env.yaml            <- PLACEHOLDER, seal before committing
    deployment.api.yaml        <- Deployment + ServiceAccount + PDB
    deployment.worker.yaml     <- Deployment + ServiceAccount + PDB
    deployment.beat.yaml       <- Deployment + ServiceAccount (singleton)
    service.api.yaml
    hpa.api.yaml
    ingress.yaml               <- cert-manager + ingress-nginx
    networkpolicy.yaml         <- default-deny + explicit allow-lists
    kustomization.yaml
  overlays/                    <- per-environment overrides (create as needed)
    dev/
      kustomization.yaml
      configmap.patch.yaml
      sealed-secret.env.yaml
    staging/
    prod/
```

Each overlay pins the image tag (`newTag: sha-<git-sha>`), overrides
`ALLOWED_HOSTS`, patches replica counts, and swaps the placeholder Secret for a
kubeseal-generated `SealedSecret`.

## Apply an overlay

```bash
kubectl apply -k deploy/k8s/overlays/prod
```

Dry-run first:

```bash
kubectl kustomize deploy/k8s/overlays/prod | kubectl diff -f -
```

## Cluster prerequisites (install once)

1. **ingress-nginx** — required by `ingress.yaml`.
   ```bash
   helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
   helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
     --namespace ingress-nginx --create-namespace \
     --set controller.metrics.enabled=true
   ```

2. **cert-manager + ClusterIssuer** — required by the Ingress cert-manager
   annotation.
   ```bash
   helm repo add jetstack https://charts.jetstack.io
   helm upgrade --install cert-manager jetstack/cert-manager \
     --namespace cert-manager --create-namespace \
     --set crds.enabled=true

   # Then apply a ClusterIssuer named `letsencrypt-prod` — see cert-manager
   # docs for the ACME issuer template.
   ```

3. **sealed-secrets** — required to seal `secret.env.yaml` before committing.
   ```bash
   helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
   helm upgrade --install sealed-secrets sealed-secrets/sealed-secrets \
     --namespace kube-system

   # Install the kubeseal CLI locally, then seal the template:
   kubeseal --format=yaml \
     --controller-namespace=kube-system \
     --controller-name=sealed-secrets-controller \
     < deploy/k8s/base/secret.env.yaml \
     > deploy/k8s/overlays/prod/sealed-secret.env.yaml
   ```

4. **PodSecurity Admission (restricted)** — the base `namespace.yaml` already
   sets `pod-security.kubernetes.io/enforce=restricted`. Verify the cluster is
   at Kubernetes 1.25+ so PSA is GA.

5. **metrics-server** — required by `hpa.api.yaml` (CPU/memory metrics).
   ```bash
   helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/
   helm upgrade --install metrics-server metrics-server/metrics-server \
     --namespace kube-system
   ```

6. **Optional but recommended**
   - `kube-prometheus-stack` for scraping the `prometheus.io/*` annotations on
     the API pods.
   - `external-secrets` or Vault CSI as an alternative to sealed-secrets.

## Local tooling

Install once on the workstation that will run the applies:

| Tool                | Purpose                                      |
|---------------------|----------------------------------------------|
| `kubectl` >= 1.28   | Apply manifests, roll out, debug pods        |
| `kustomize` >= 5.0  | Bundled with kubectl but keep standalone too |
| `helm` >= 3.14      | Install ingress-nginx / cert-manager / etc.  |
| `kubeseal` >= 0.25  | Seal `Secret` -> `SealedSecret` before commit|
| `cosign` >= 2.2     | Verify signed images before promotion        |

## Verifying an image before promotion

The `build-and-push` workflow signs images with cosign (keyless when
`COSIGN_EXPERIMENTAL=1` or with a key stored as `COSIGN_KEY`). Verify before
promoting an overlay to the next environment:

```bash
cosign verify \
  --certificate-identity-regexp 'https://github.com/cybercom/cymed' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  ghcr.io/cybercom/cymed-api:sha-<git-sha>
```
