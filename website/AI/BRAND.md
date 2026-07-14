# Brand Identity

## Company

**Name:** CyberCom Revolution
**Tagline:** Transforming Healthcare, Government & Enterprise
**Domain:** cy-com.com
**Products domain:** cymed.cy-com.com (CyMed), app.cy-com.com (platform)

---

## Product Names

| Platform | Short Name | Full Name |
|----------|-----------|-----------|
| Healthcare | CyMed | CyMed Healthcare Platform |
| ERP | CyCom | CyCom Enterprise ERP |
| Government | CyGov | CyGov Government Platform |
| Identity | CyIdentity | CyIdentity IAM |
| Integration | CyIntegrationHub | CyIntegrationHub |
| AI | CyAI | CyAI Intelligence Platform |
| Analytics | CyData | CyData Analytics Platform |
| Communications | CyConnect | CyConnect Communications |
| Citizen | CyCitizen | CyCitizen Services |

Always use the correct casing: `CyMed` not `Cymed` or `CYMED`.

---

## Visual Design System

### Color Palette (Tailwind classes used in codebase)

| Color | Usage |
|-------|-------|
| `emerald-400/500` | Healthcare / CyMed |
| `blue-400/500` | Enterprise / Platform |
| `pink-400/500` | AI / Intelligence |
| `purple-400/500` | Government / CyGov |
| `slate-900/950` | Dark backgrounds |
| `slate-800` | Card backgrounds |
| `slate-700` | Border/divider colors |
| `white` | Primary text on dark |
| `slate-400` | Secondary text |

### Design Style

- **Mode:** Dark-first (dark background, light text)
- **Feel:** Professional, technical, modern — not consumer/playful
- **Depth:** Subtle gradients, glassmorphism effects for cards
- **Borders:** Low-opacity colored borders (`border-emerald-500/20`)
- **Backgrounds:** Semi-transparent overlays (`bg-emerald-500/5`)
- **Typography:** Professional system fonts or premium web fonts

### Product Color Coding

Each product family has a consistent color:
- Healthcare products → `emerald` green
- Enterprise/ERP products → `blue`
- Intelligence/AI/Data → `pink`
- Government/Citizen → `purple`
- Platform services (Identity, Integration, Connect) → `blue`/`slate`

---

## Typography

- Headlines: Bold, large scale — establish authority
- Body: Regular weight, comfortable reading
- Technical terms: Use code formatting when referencing standards (FHIR, ICD-11, etc.)
- Arabic: Use RTL-compatible font stack, ensure proper Arabic numeral handling

---

## Tone of Voice

- **Professional:** This is enterprise B2B software, not consumer
- **Authoritative:** CyberCom is a platform leader, not a startup
- **Clear:** No jargon for jargon's sake — explain clinical/technical terms briefly
- **Confident:** State capabilities directly, avoid hedging language
- **Global:** Culturally neutral English and native Arabic (not translated Arabic)

---

## Logo Usage

- Logo path: `/images/logo.png`
- Always use full logo on marketing pages
- White/light version on dark backgrounds
- Never stretch, recolor, or modify the logo
- Minimum clear space: 24px on all sides

---

## White Label Notes

When building reusable components, brand tokens must be configurable:
- Logo: from brand config, not hardcoded path
- Company name: from brand config
- Color: from Tailwind theme tokens, configurable per tenant
- Domain: configurable

The website itself is CyberCom branded. The platform products support white-label via `BrandingMiddleware`.

---

## Do Not

- Do not use "CyberCom" without "Revolution" on first mention on a page
- Do not use ALL CAPS for product names (`CYMED` is wrong, `CyMed` is correct)
- Do not mix color coding (don't use blue for healthcare)
- Do not use bright/saturated background colors — dark palette only
- Do not use consumer-style language ("Easy!", "Awesome!") in enterprise contexts
