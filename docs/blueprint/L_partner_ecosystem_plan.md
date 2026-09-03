# Section L — Partner & Ecosystem Integration Plan

> The "active ecosystem of partners" constraint from Section A. What CyberCom integrates,
> in what order, commercial shape, and build effort. All via `platform/cyintegrationhub`
> (connector framework + credential vault + retry/DLQ + webhook delivery).

## L.1 Integration categories & priority

| Category | Why it matters | Wave | Owner |
|---|---|---|---|
| Payments (PSP) | blocks paid self-serve; PCI scope | 1 | Payments pod |
| E-invoicing / tax portals | legal to operate (ZATCA etc.) | 1 | Finance pod |
| Delivery / logistics | Retail/Grocery flavor value | 2 | Retail pod |
| Payroll / WPS banks | payroll compliance | 2 | HR pod |
| Government identity | onboarding trust, gov flavor | 2–3 | Platform pod |
| Health networks (claims/HIE) | HealthFlavour operation | 2–3 | Health pod |
| Labs / pharmacies / insurers | HealthFlavour depth | 3 | Health pod |
| Accounting / BI exports | buyer switching cost reducer | 3 | Finance pod |
| Marketplace / connector devs | ecosystem revenue | 4–5 | Platform pod |

## L.2 Payments (PSP)

| Partner | Coverage | Why | Integration | Commercials |
|---|---|---|---|---|
| **HyperPay** | KSA, UAE, JO, wider MENA | broad regional acquirer coverage, mada/KNET/benefit, tokenisation | REST + hosted checkout + webhooks; tokenise (no PAN on our side) | per-txn MDR passed through or marked up; partner/ISO agreement |
| **PayTabs** | KSA, UAE, JO, EG | strong SMB onboarding, split payments | REST + iframe + webhooks | same |
| **Moyasar** | KSA-focused | clean API, mada + Apple Pay, fast KSA onboarding | REST + webhooks | per-txn |
| **Tap Payments** | GCC-wide | good DX, GoSell, KNET/benefit/mada | REST + webhooks | per-txn |
| **Stripe** | international cards | non-GCC customers, subscription billing for the platform itself | Billing + PaymentIntents + webhooks (HMAC verify — already built) | standard |

- **Abstraction:** one `PaymentProvider` interface (evolve from CyMart `payments`); providers are config per tenant/region. Refunds, disputes, partial capture, 3-DS all in the interface.
- **PCI:** SAQ-A posture — card data entered in PSP-hosted fields/iframe, we store only tokens + last4 + brand.
- **Order:** wire Moyasar **or** HyperPay first (Phase 1, decision O7), add the rest by Phase 3.
- **Settlement/payout** (for CyMart marketplace + delivery): use PSP split-payment or a dedicated payout rail; reconcile in `settlement` ledger.

## L.3 E-invoicing / tax portals

| Portal | Country | Model | Status | Build |
|---|---|---|---|---|
| **ZATCA Fatoora** | KSA | Phase 2 clearance — UBL 2.1 XML, CSID, cryptographic stamp, QR, hash chain, real-time clearance API | **P0, net-new** | XML generator + CSID onboarding + clearance/reporting client + archival (CyVault). Certified Solution Provider path where beneficial. |
| **JoFotara** | **Jordan** | national e-invoicing platform (ISTD) — invoice submission + clearance, QR, JSON/UBL payload, taxpayer + activity registration, client-credentials auth | **P0 — Jordan is a launch market** | Clearance mode `JO_JOFOTARA` in the shared engine; taxpayer onboarding + submission/ack client + archival (CyVault). A `cymed/products/cymed/integrations/jofawtra` module already exists — fold it into the shared clearance engine, don't keep it CyMed-local. |
| **UAE e-invoicing** | UAE | Peppol-based, phased federal rollout | monitor go-live | mode `AE_PEPPOL` (Peppol Access Point — partner or self-accredit) |

- Design the clearance engine **mode-pluggable** from day one; adding a country = a mode + a connector, no core change (J.1 A9).
- **Jordan is a first-class launch market, not "later".** `JO_JOFOTARA` ships alongside `SA_ZATCA` in Phase 1; every flavor that transacts in JO declares `regulatory: [jo_jofotara]`. The JO beachhead in the go-to-market plan depends on this being real.

## L.4 Delivery / logistics

| Partner | Region | Integration | Notes |
|---|---|---|---|
| **CyDrive** (own) | — | direct (internal dispatch API) | first-party; already seam-wired to CyMart |
| **Talabat** | GCC-wide | menu/catalog push, order webhook pull, status sync, menu availability | largest GCC aggregator; partner API access required |
| **Jahez** | KSA | order integration API | KSA leader |
| **HungerStation** | KSA | order integration | KSA |
| **Deliveroo** | UAE, KW, QA | order integration | UAE presence |
| **Careem / Careem Box** | GCC | rides + delivery | optional |
| **Aramex / SMSA / Fetchr / iMile** | GCC parcel | shipment booking, label, tracking webhook | for e-commerce fulfilment (non-food) |

- **Aggregator sync service**: normalises menu push + order pull across providers to one internal model; per-branch enable/disable; menu/price/availability drift reconciliation.
- Priority: CyDrive (Phase 2) → Talabat + Jahez (Phase 2–3) → rest on demand.

## L.5 Payroll / WPS

| Country | System | Integration |
|---|---|---|
| KSA | **Mudad / WPS** via banks; GOSI | generate WPS SIF file; GOSI contribution calc (profile `SA_GOSI`) |
| UAE | **WPS** via agent banks (Central Bank) | SIF generator; GPSSA for nationals; gratuity calc |
| Jordan | Social Security Corporation | contribution file + reporting |

- WPS SIF generators are **net-new** (payroll calc exists). Bank-specific SIF format variations handled by templates.

## L.6 Government identity & portals

| Portal | Country | Use |
|---|---|---|
| **Nafath** | KSA | citizen/business identity verification at onboarding; gov flavor login |
| **Absher Business** | KSA | business verification |
| **UAE PASS** | UAE | identity verification |
| **MoHRE** | UAE | labour contract validation |
| **Sanad / national e-gov** | Jordan | citizen services (gov flavor) |

- Via `cyintegrationhub` connectors; used by provisioning (verify CR/VAT number) and GovernmentPortalFlavour.

## L.7 Health networks

| Partner | Country | Use |
|---|---|---|
| **NPHIES** | KSA | eligibility, pre-auth, claims, communication — mandatory for KSA health billing |
| **Riayati / Malaffi / NABIDH** | UAE (federal/AbuDhabi/Dubai HIE) | health information exchange |
| **DHA eClaim / DoH** | UAE emirates | claims submission |
| **SEHA / insurers (Bupa, Tawuniya, Daman, etc.)** | GCC | direct payer integrations / TPA portals |
| **SFDA / MoH drug registries** | KSA | drug master data, controlled substances |
| Lab / pharmacy chains | GCC | referral orders, results, dispensing |

- HealthFlavour RCM → NPHIES connector is the P0 for KSA health. UAE emirate connectors Phase 3.

## L.8 Accounting / BI / misc

| Partner | Use |
|---|---|
| QuickBooks / Xero / Zoho Books export | let buyers keep their accountant's tool during transition (reduces switching friction) |
| Power BI / Looker / Metabase connectors | enterprise analytics on the read-model |
| WhatsApp Business API (Meta / Twilio / Unifonic /360dialog) | notifications, order updates, appointment reminders, receipts |
| SMS (Unifonic, Taqnyat, Twilio) | OTP, reminders |
| Email (SES / Postmark) | transactional |
| Maps (Google / Mapbox) | delivery zones, branch locator |

## L.9 Partner programme (commercial)

| Track | Who | Model |
|---|---|---|
| **Implementation partners** | regional ERP consultancies, accountants, POS resellers | referral fee + revenue share on managed accounts; partner portal (Phase 4) with leads, training, sandbox |
| **Technology / connector partners** | ISVs building on the API | listed in the connector marketplace; revenue share on paid connectors (Phase 5) |
| **PSP / delivery / telco** | as above | ISO/reseller agreements; co-marketing; bundled pricing |
| **Anchor customers** | multi-branch groups, hospital networks | design-partner terms (discount for reference + case study + roadmap input) |

- **Sequencing:** direct-sold + high-touch through Retail GA (Phase 2). Formalise the implementation-partner programme at Phase 4 (once onboarding is automated enough to hand off). Connector marketplace at Phase 5.

## L.10 Connector build backlog (ordered)

1. PSP #1 (Moyasar or HyperPay) — Phase 1
2. ZATCA Fatoora clearance — Phase 1
3. Keycloak/CyIdentity consolidation (internal) — Phase 1
4. Stripe (platform billing) — Phase 1
5. CyDrive dispatch — Phase 2
6. WhatsApp + SMS + Email — Phase 2
7. PSP #2–3 — Phase 2
8. WPS SIF (KSA, UAE) — Phase 2
9. Talabat + Jahez — Phase 2–3
10. NPHIES — Phase 3
11. Nafath / UAE PASS — Phase 3
12. JoFotara, AE Peppol AP — Phase 3
13. Accounting exports (QuickBooks/Xero/Zoho) — Phase 3
14. UAE emirate health (Riayati/Malaffi/DHA) — Phase 3
15. BI connectors + marketplace SDK — Phase 4–5
