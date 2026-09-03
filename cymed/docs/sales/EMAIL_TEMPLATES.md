---
title: CyMed Sales Email Templates
version: 1.0
date: 2026-08-26
owner: Cybercom sales enablement
audience: AE / SDR
region: Jordan first; KSA & UAE next
---

# CyMed Email Templates

Eight reusable email templates for the CyMed sales team. Copy-paste, swap the `{{placeholders}}`, send.

## Placeholder cheat sheet

| Placeholder | Meaning | Example |
|---|---|---|
| `{{first_name}}` | Recipient first name | Rania |
| `{{title}}` | Their title | Chief Medical Officer |
| `{{hospital}}` | Their organization | Specialized Hospital Amman |
| `{{module}}` | The single CyMed module most relevant to their pain | NPHIES-integrated RCM |
| `{{ae_name}}` | Sending rep | Mohammed Alnsour |
| `{{ae_mobile}}` | Sending rep mobile (WhatsApp-ready) | +962 7X XXX XXXX |
| `{{meeting_date}}` | Date of last meeting | 24 Aug 2026 |

## Related docs

- [Elevator pitch](./ELEVATOR_PITCH.md)
- [Pricing sheet](./PRICING.md)
- [90-day paid pilot agreement](./PILOT_AGREEMENT.md)
- [Cloud demo](https://claude.ai/code/artifact/4ea40b02-e12b-4d84-a37e-a9aa3cb95656)
- [UAT checklist](https://claude.ai/code/artifact/8396ce53-4c23-4908-8a0d-64a616a24e69)

## Template index

| # | Template | Trigger | Target |
|---|---|---|---|
| 1 | Cold intro — CMO / CIO | First outreach, clinical / IT owner | CMO, CIO, COO |
| 2 | Cold intro — CFO | First outreach, financial owner | CFO, Finance Director |
| 3 | LinkedIn connection | InMail-style, < 300 chars | Any exec |
| 4 | Post-demo follow-up | Same-day after demo | All demo attendees |
| 5 | Nurture — 2 weeks silent | No reply after demo / follow-up | Warm but silent |
| 6 | Technical follow-up | After IT / SE meeting | CIO, IT Director, HIS Manager |
| 7 | Pilot proposal | Buyer asked for terms | Economic buyer |
| 8 | Breakup email | 3 attempts, no reply | Closing the loop warmly |

---

## 1. Cold intro — CMO / CIO · pain-based hook

**Purpose.** First touch to a clinical or IT owner. Lead with a specific operational pain, not a product pitch.

**Subject line options**

| # | English | Arabic |
|---|---|---|
| A | `{{hospital}} — NPHIES rejections cutting into revenue?` | `{{hospital}} — رفوضات نفيس تستنزف الإيرادات؟` |
| B | `39 modules on one platform for {{hospital}}` | `39 وحدة على منصة واحدة لـ {{hospital}}` |
| C | `Ambient AI scribe pilot for {{hospital}} clinicians` | `تجربة كاتب طبي بالذكاء الاصطناعي لأطباء {{hospital}}` |

### Body — English

Dear Dr. {{first_name}},

I lead CyMed at Cybercom — a Middle-East-native healthcare platform now live with Jordanian and Saudi providers. Three questions we hear from CMOs and CIOs like you:

- Are your clinicians spending more than 90 minutes per shift on documentation? *(illustrative)*
- Is your NPHIES / JoFotara rejection rate above 8%? *(illustrative)*
- Are you running 4+ vendors for EMR, LIS, RIS, pharmacy, and RCM?

CyMed replaces that stack with a single platform — 39 modules across reception, ED, ICU, OR, NICU, lab, imaging, pharmacy, RCM, HR, quality, patient app, and exec dashboards. Aligned with JCI, HCAC, CBAHI, SFDA and CCHI on day one.

Would 25 minutes next week work for a walkthrough scoped to **{{module}}**?

Kind regards,
{{ae_name}}

### Body — Arabic

الدكتور/ة {{first_name}} المحترم/ة،

أقود منتج CyMed لدى Cybercom، وهو منصة رعاية صحية مصممة للمنطقة العربية ومستخدَمة حالياً في مزوّدين خدمة في الأردن والسعودية. ثلاثة أسئلة نسمعها من المديرين الطبيين ومديري تقنية المعلومات:

- هل يستهلك الأطباء لديكم أكثر من 90 دقيقة في كل مناوبة على التوثيق؟ *(رقم توضيحي)*
- هل تتجاوز نسبة رفوضات NPHIES / JoFotara لديكم 8%؟ *(رقم توضيحي)*
- هل تعتمدون على أربعة موردين أو أكثر بين EMR وLIS وRIS والصيدلية ودورة الإيرادات؟

يحل CyMed محل هذه المنظومة بمنصة واحدة تضم 39 وحدة تغطي الاستقبال والطوارئ والعناية المركزة وغرف العمليات وحديثي الولادة والمختبر والأشعة والصيدلية ودورة الإيرادات والموارد البشرية والجودة وتطبيق المريض ولوحات الإدارة. متوافقة مع JCI وHCAC وCBAHI وSFDA وCCHI منذ اليوم الأول.

هل يناسبكم لقاء لمدة 25 دقيقة الأسبوع القادم لعرض مركّز حول **{{module}}**؟

مع الاحترام،
{{ae_name}}

### PS

> **PS.** Two-minute cloud demo (no login): https://claude.ai/code/artifact/4ea40b02-e12b-4d84-a37e-a9aa3cb95656 · ملاحظة: عرض تجريبي سحابي (دقيقتان، بدون تسجيل دخول).

### Signature

```
{{ae_name}}
CyMed — a Cybercom product
{{ae_mobile}} · cymed@cybercom.jo
Amman · Riyadh · Dubai
```

---

## 2. Cold intro — CFO · financial hook

**Purpose.** First touch to the economic buyer. Numbers first, product second.

**Subject line options**

| # | English | Arabic |
|---|---|---|
| A | `{{hospital}} — recover 3-4% of net revenue from denials?` | `{{hospital}} — استرداد 3-4% من صافي الإيرادات من الرفوضات؟` |
| B | `DSO benchmark for {{hospital}} vs regional peers` | `قياس أيام التحصيل لـ {{hospital}} مقارنة بالمنطقة` |
| C | `One vendor, 39 modules — CFO briefing for {{hospital}}` | `مزوّد واحد و39 وحدة — إحاطة للمدير المالي {{hospital}}` |

### Body — English

Dear {{first_name}},

Two numbers we track across Middle-East hospitals on CyMed:

| Metric | Regional benchmark *(illustrative)* | CyMed customers *(illustrative)* |
|---|---|---|
| DSO (days sales outstanding) | 68 days | 41 days |
| First-pass denial rate | 11% | 4% |
| RCM staff cost as % of net revenue | 3.2% | 1.9% |

CyMed collapses EMR, LIS, RIS, pharmacy, HR, and RCM onto one platform, with NPHIES, JoFotara, CCHI, and HyperPay pre-integrated. Result: fewer vendors, fewer denials, faster cash.

I would welcome 20 minutes to share a written business case scoped to **{{hospital}}** — active providers, claim volume, payer mix. Would next Wednesday or Thursday work?

Kind regards,
{{ae_name}}

### Body — Arabic

الأستاذ/ة {{first_name}} المحترم/ة،

رقمان نقيسهما لدى مستشفيات المنطقة على CyMed:

| المؤشر | المتوسط الإقليمي *(توضيحي)* | عملاء CyMed *(توضيحي)* |
|---|---|---|
| أيام التحصيل (DSO) | 68 يوم | 41 يوم |
| نسبة الرفض من أول تقديم | 11% | 4% |
| كلفة موظفي دورة الإيرادات كنسبة من صافي الإيرادات | 3.2% | 1.9% |

يجمع CyMed EMR وLIS وRIS والصيدلية والموارد البشرية ودورة الإيرادات في منصة واحدة، مع تكامل جاهز مع NPHIES وJoFotara وCCHI وHyperPay. النتيجة: عدد أقل من الموردين، رفوضات أقل، وتدفق نقدي أسرع.

نطلب 20 دقيقة لتقديم دراسة جدوى مكتوبة مخصصة لـ **{{hospital}}** بناءً على عدد الأطباء وحجم المطالبات والدافعين. هل يناسبكم الأربعاء أو الخميس القادم؟

مع الاحترام،
{{ae_name}}

### PS

> **PS.** Reference: our 90-day paid pilot ties fees to your denial-rate target — see [pilot terms](./PILOT_AGREEMENT.md). ملاحظة: التجربة المدفوعة لمدة 90 يوم مرتبطة بهدف نسبة الرفض لديكم.

### Signature

```
{{ae_name}}
CyMed — a Cybercom product
{{ae_mobile}} · cymed@cybercom.jo
```

---

## 3. LinkedIn connection message — under 300 chars

**Purpose.** Warm the target before the first email. Character budget is enforced by LinkedIn (300 max). Templates below are counted.

### Variant A — CMO / CIO (EN, 268 chars)

```
Dr. {{first_name}}, I lead CyMed at Cybercom — a single-platform EMR + RCM
built for the Middle East (NPHIES, JoFotara, Arabic RTL, ambient AI scribe).
Live in JO and KSA. Would value connecting — happy to share a 2-min demo if
it is useful for {{hospital}}.
```

### Variant A — CMO / CIO (AR, 288 chars)

```
د. {{first_name}}، أقود CyMed لدى Cybercom — منصة EMR ودورة إيرادات موحدة
مبنية للمنطقة العربية (نفيس، JoFotara، عربية RTL، كاتب طبي بالذكاء
الاصطناعي). قيد التشغيل في الأردن والسعودية. سعيد بالتواصل — يسرني مشاركة
عرض دقيقتين إن كان مفيداً لـ {{hospital}}.
```

### Variant B — CFO (EN, 264 chars)

```
{{first_name}}, CyMed customers cut first-pass denials from ~11% to ~4% and
DSO from ~68 to ~41 days (illustrative). One platform, NPHIES + JoFotara
built in. Would value connecting and sharing the benchmark deck for
{{hospital}}.
```

### Variant B — CFO (AR, 279 chars)

```
{{first_name}}، عملاء CyMed خفّضوا رفض المطالبات من أول تقديم من ~11% إلى
~4% وأيام التحصيل من ~68 إلى ~41 يوم (توضيحي). منصة موحدة مع نفيس
وJoFotara جاهزَين. سعيد بالتواصل ومشاركة مقارنة معيارية لـ {{hospital}}.
```

**Rule of thumb.** Never paste a demo link in the first LinkedIn message — send it after they accept.

---

## 4. Post-demo follow-up — same day

**Purpose.** Send within 4 hours of the demo. Recap, next step, remove friction.

**Subject line**

| English | Arabic |
|---|---|
| `Recap + next step — CyMed for {{hospital}}` | `ملخص وخطوة تالية — CyMed لـ {{hospital}}` |

### Body — English

Dear {{first_name}},

Thank you for the time today. Quick recap of what we agreed:

| Item | Owner | Date |
|---|---|---|
| CyMed to share sandbox access for **{{module}}** | {{ae_name}} | Within 24h |
| {{hospital}} to share sample de-identified claims dataset | {{first_name}}'s team | By {{meeting_date}} + 5 |
| Joint technical session with your HIS / IT lead | Both | To be scheduled this week |
| Draft 90-day paid pilot scope | {{ae_name}} | Within 5 business days |

Three items you asked about, answered:

1. **NPHIES / JoFotara.** Pre-built, in production. Certification packs on request.
2. **Data residency.** Choose cloud (JO region), on-prem, or hybrid — your call, contracted.
3. **Arabic + RTL.** Full stack, not translated. Clinical notes, prescriptions, and patient app all bilingual.

Sandbox login and the [UAT checklist](https://claude.ai/code/artifact/8396ce53-4c23-4908-8a0d-64a616a24e69) go out separately in the next hour.

Kind regards,
{{ae_name}}

### Body — Arabic

الدكتور/ة {{first_name}} المحترم/ة،

شكراً على وقتكم اليوم. ملخص لما تم الاتفاق عليه:

| البند | المسؤول | التاريخ |
|---|---|---|
| مشاركة صلاحية بيئة تجريبية لوحدة **{{module}}** | {{ae_name}} | خلال 24 ساعة |
| مشاركة عيّنة مطالبات غير مُعرِّفة | فريق {{first_name}} | بحلول {{meeting_date}} + 5 |
| جلسة تقنية مشتركة مع مسؤول HIS / IT | الطرفان | خلال الأسبوع |
| مسودة نطاق التجربة المدفوعة لمدة 90 يوم | {{ae_name}} | خلال 5 أيام عمل |

ثلاث نقاط استفسرتم عنها:

1. **نفيس / JoFotara.** مبنية مسبقاً، قيد التشغيل. حزم الاعتماد متاحة عند الطلب.
2. **مكان تخزين البيانات.** سحابي (منطقة الأردن) أو محلي أو هجين — الاختيار لكم، ويُوثَّق في العقد.
3. **العربية وRTL.** مبنية أصلاً وليست ترجمة. الملاحظات السريرية والوصفات وتطبيق المريض جميعها ثنائية اللغة.

سيصلكم منفصلاً خلال الساعة القادمة رابط البيئة التجريبية و[قائمة اختبار القبول](https://claude.ai/code/artifact/8396ce53-4c23-4908-8a0d-64a616a24e69).

مع الاحترام،
{{ae_name}}

### PS

> **PS.** If it helps, I can join a 15-minute call tomorrow with your medical director to answer clinical-workflow questions on **{{module}}**. ملاحظة: يسرّني الانضمام غداً لمكالمة 15 دقيقة مع المدير الطبي للإجابة عن أسئلة سير العمل السريري.

### Signature

```
{{ae_name}}
CyMed — a Cybercom product
{{ae_mobile}} · cymed@cybercom.jo
```

---

## 5. Nurture — 2 weeks silent, sending industry insight

**Purpose.** Buyer went dark. Do not chase. Send value.

**Subject line options**

| # | English | Arabic |
|---|---|---|
| A | `NPHIES v3 rule changes — impact on {{hospital}}` | `تعديلات نفيس v3 — الأثر على {{hospital}}` |
| B | `Ambient scribe — 12-week clinician time study` | `الكاتب الطبي بالذكاء الاصطناعي — دراسة 12 أسبوع` |
| C | `HCAC 2027 update — the 3 changes that matter` | `تحديث HCAC 2027 — التغييرات الثلاثة المهمة` |

### Body — English

Dear {{first_name}},

Not chasing — sharing.

We published a short brief this week on three regulatory shifts that will affect any Jordanian or Saudi provider in 2027:

- **NPHIES v3.** New pre-auth data elements; roughly 40% of current claim templates will need re-mapping. *(illustrative)*
- **HCAC 2027 standards.** Nursing documentation and medication reconciliation are the two most rewritten chapters.
- **SFDA e-prescription mandate.** Full traceability required for controlled substances by Q3 2027.

Two-page brief, no marketing, no gate: [Download the brief](./NPHIES_HCAC_SFDA_2027_BRIEF.pdf) *(link illustrative)*.

If any of these hit {{hospital}}'s roadmap, happy to compare notes — no pitch. Just a call between two people who care about the same things.

Kind regards,
{{ae_name}}

### Body — Arabic

الدكتور/ة {{first_name}} المحترم/ة،

لست ألاحق — أشارك.

أصدرنا هذا الأسبوع ملخصاً مختصراً حول ثلاثة تحوّلات تنظيمية ستؤثر على أي مزوّد أردني أو سعودي في 2027:

- **نفيس v3.** بنود بيانات جديدة للموافقة المسبقة؛ نحو 40% من قوالب المطالبات الحالية ستحتاج إعادة تخطيط. *(توضيحي)*
- **معايير HCAC 2027.** فصلا التوثيق التمريضي ومطابقة الأدوية هما الأكثر إعادة كتابة.
- **إلزام الوصفة الإلكترونية من SFDA.** تتبّع كامل مطلوب للمواد الخاضعة للرقابة بحلول الربع الثالث من 2027.

الملخص من صفحتين، بلا تسويق وبلا تسجيل: [تحميل الملخص](./NPHIES_HCAC_SFDA_2027_BRIEF.pdf) *(رابط توضيحي)*.

إن كان أي من هذه التغييرات ضمن خارطة طريق {{hospital}}، يسرّني تبادل الملاحظات بلا عرض بيع — مجرد مكالمة بين شخصين يهتمّان بذات المواضيع.

مع الاحترام،
{{ae_name}}

### PS

> **PS.** Also happy to introduce you to Dr. [reference customer] at [reference hospital] if a peer conversation is useful. ملاحظة: يسرّني تعريفكم بأحد عملائنا المرجعيين إن كانت المحادثة مع نظير مفيدة.

### Signature

```
{{ae_name}}
CyMed — a Cybercom product
{{ae_mobile}} · cymed@cybercom.jo
```

---

## 6. Technical follow-up — after IT / SE meeting

**Purpose.** IT team met the SE. Answer the open questions in writing, keep IT the champion, hand back to the exec buyer.

**Subject line**

| English | Arabic |
|---|---|
| `Answers to open technical questions — CyMed at {{hospital}}` | `إجابات الأسئلة التقنية المفتوحة — CyMed في {{hospital}}` |

### Body — English

Dear {{first_name}},

Following the technical session with your team on {{meeting_date}}, here are written answers to the seven open items. Please share with your architects.

| # | Topic | CyMed answer |
|---|---|---|
| 1 | Data residency | Cloud (Jordan region, sovereign), on-prem, or hybrid. Choice is contractual. |
| 2 | Backup / DR | RPO 15 min, RTO 4 h *(illustrative — actual per SLA)*. Geo-redundant to secondary JO region. |
| 3 | Interoperability | HL7 v2, FHIR R4, DICOM, IHE profiles. NPHIES, JoFotara, Hakeem, WHO ICD-11 pre-built. |
| 4 | Identity / SSO | SAML 2.0, OIDC, Azure AD, on-prem AD. Break-glass and MFA enforceable per role. |
| 5 | Audit / compliance | Immutable audit log; HIPAA-aligned; JCI / HCAC / CBAHI reports pre-configured. |
| 6 | Deployment | Kubernetes-native. Air-gapped install option for on-prem. |
| 7 | Data export | Any PHI table exportable to CSV, Parquet, FHIR bundle. No lock-in clause is in the MSA. |

**Two artifacts attached** (in the follow-up email, not this one):

1. Architecture diagram — one page
2. Security control matrix mapped to HIPAA, ISO 27001, HITRUST

Next step: I propose a 45-minute session with your CISO and Head of Infrastructure to walk the security control matrix and agree the pilot's technical scope. Would week of {{meeting_date}} + 7 work?

Kind regards,
{{ae_name}}

### PS

> **PS.** Sandbox access is still live at the URL you were sent — happy to extend it another 30 days if useful.

### Signature

```
{{ae_name}}
CyMed — a Cybercom product
{{ae_mobile}} · cymed@cybercom.jo
```

---

## 7. Pilot proposal — attaching PILOT_AGREEMENT.md and PRICING.md

**Purpose.** Buyer asked for terms. Send the paper. Anchor on outcome, not price.

**Subject line**

| English | Arabic |
|---|---|
| `90-day paid pilot proposal — CyMed for {{hospital}}` | `مقترح تجربة مدفوعة لمدة 90 يوم — CyMed لـ {{hospital}}` |

### Body — English

Dear {{first_name}},

Per your request, attached is the 90-day paid pilot proposal for {{hospital}}. Two documents:

| Document | What is inside |
|---|---|
| [PILOT_AGREEMENT.md](./PILOT_AGREEMENT.md) | Scope, success criteria, exit terms, data ownership, MSA / BAA / DPA references |
| [PRICING.md](./PRICING.md) | Per-active-provider tier for Clinic/Hospital; per-room / per-workstation for ancillary; Pilot / Standard / Enterprise bands |

### Pilot at a glance

| Item | Proposal |
|---|---|
| Duration | 90 days, paid, fixed fee |
| Scope | **{{module}}** + Reception + RCM (NPHIES / JoFotara live) |
| Users | Up to 25 active providers *(adjustable)* |
| Success criteria | 30% documentation-time reduction; first-pass denial rate below 6% *(illustrative)* |
| Data | 100% yours. Full export on any exit. |
| Exit | Either party may exit at day 60 for cause; refund schedule in agreement |
| Path to production | Pilot fee credits 50% toward year-one Standard licence if you continue |

### What we need from you to start

- Countersigned pilot agreement
- List of pilot providers and departments
- IT contact for sandbox provisioning
- Payer contract copies (for NPHIES / JoFotara scope confirmation)

Kickoff can be within 10 business days of countersignature.

Kind regards,
{{ae_name}}

### PS

> **PS.** Legal and clinical redlines welcome — MSA, BAA, and DPA are Middle-East-adapted templates and we expect edits.

### Signature

```
{{ae_name}}
CyMed — a Cybercom product
{{ae_mobile}} · cymed@cybercom.jo
```

---

## 8. Breakup email — 3 attempts, no reply

**Purpose.** Close the loop with warmth. This email frequently gets a reply.

**Subject line options**

| # | English | Arabic |
|---|---|---|
| A | `Closing the loop — {{hospital}}` | `إغلاق الملف — {{hospital}}` |
| B | `Should I stop reaching out?` | `هل أتوقف عن التواصل؟` |
| C | `One last note on CyMed for {{hospital}}` | `ملاحظة أخيرة حول CyMed لـ {{hospital}}` |

### Body — English

Dear {{first_name}},

I have written three times over the past six weeks and understand life is busy — no offence taken by the silence.

I will stop reaching out after this note. Two things before I do:

1. **The door stays open.** When {{hospital}} is ready to look at consolidating EMR, RCM, LIS, RIS, and pharmacy onto one Middle-East-native platform, we will be here.
2. **A parting gift.** Our internal benchmark on NPHIES first-pass denial rates across 12 regional hospitals — no marketing, no gate, useful as an internal reference: [Download the benchmark](./NPHIES_DENIALS_BENCHMARK.pdf) *(link illustrative)*.

If the timing was simply wrong, a one-line reply telling me "circle back in Q2" is all I need to keep you in a quiet quarterly loop.

Wishing you and the team at {{hospital}} a strong quarter.

Kind regards,
{{ae_name}}

### Body — Arabic

الدكتور/ة {{first_name}} المحترم/ة،

راسلتكم ثلاث مرات خلال الأسابيع الستة الماضية، وأتفهّم انشغالكم تماماً — لا اعتراض على الصمت.

سأتوقف عن التواصل بعد هذه الرسالة. ملاحظتان قبل ذلك:

1. **الباب يبقى مفتوحاً.** حين يصبح {{hospital}} جاهزاً للنظر في توحيد EMR ودورة الإيرادات والمختبر والأشعة والصيدلية في منصة واحدة مبنية للمنطقة العربية، سنكون في الخدمة.
2. **هدية وداع.** دراستنا الداخلية لنسب رفض المطالبات من أول تقديم عبر 12 مستشفى إقليمي — بلا تسويق وبلا تسجيل، مفيدة كمرجع داخلي: [تحميل الدراسة](./NPHIES_DENIALS_BENCHMARK.pdf) *(رابط توضيحي)*.

إن كان التوقيت هو المشكلة فقط، يكفي سطر واحد "عاود التواصل في الربع الثاني" لأبقيكم ضمن حلقة ربع سنوية هادئة.

أطيب التمنيات لكم ولفريق {{hospital}} بربع سنوي قوي.

مع الاحترام،
{{ae_name}}

### PS

> **PS.** No response is also a response — thank you for the consideration either way. ملاحظة: عدم الرد هو أيضاً رد — شكراً على وقتكم في الحالتين.

### Signature

```
{{ae_name}}
CyMed — a Cybercom product
{{ae_mobile}} · cymed@cybercom.jo
```

---

## Sending checklist (before you hit send)

| Check | Rule |
|---|---|
| Recipient title | Use `Dr.` for clinicians, `Eng.` where appropriate, full honorific in Arabic. |
| Language pair | Send bilingual to Jordan and Saudi CMO / CIO / CFO by default. UAE English-only unless requested. |
| Placeholders | Grep the draft for `{{` before sending. Every one must be filled or removed. |
| Numbers | Any illustrative benchmark must be marked *(illustrative)* until you have the customer's own baseline. |
| Attachments | Pilot proposal is the only email that attaches the [pilot agreement](./PILOT_AGREEMENT.md) and [pricing sheet](./PRICING.md). Never attach to a cold intro. |
| Send window | Sun-Thu 08:30-10:30 local, or 15:00-17:00. Never Friday. Ramadan: after 20:00. |
| Follow-up cadence | Day 0, +3, +7, +14, then breakup at +28. Stop after breakup unless they reply. |
