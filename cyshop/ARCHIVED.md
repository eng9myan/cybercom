# Archived — 2026-09-17

CyShop is frozen. Its harvest-worthy features (RTL i18n, purchase-order
print/PDF, retail sub-type catalog work) have been ported into CyCom
(`cycom/products/cycom/`). No new feature commits go here.

The production deployment at `cyshop.cy-com.com` keeps running as-is;
archiving this source tree does not take it down. The deploy workflow
(`.github/workflows/deploy-cyshop.yml`) now only runs via manual
`workflow_dispatch`, so an edit here can no longer trigger an automatic
redeploy. Taking the live site down or migrating its data is a separate
infra decision, not made by this change.

If a real production incident needs a fix here, make the minimal patch,
deploy manually, and consider whether the equivalent fix is also needed
in CyCom.
