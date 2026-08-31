# RTL_AUDIT.md — Arabic / RTL bilingual status (Phase 2 item 6, 2026-08-25)

The buildout prompt makes RTL/Arabic a **hard requirement**. This audits where
CyCom's frontend actually stands and lays out the path to real bilingual support.
It does **not** claim the feature is done — full i18n is a sized mini-project.

## Finding: essentially greenfield

| Aspect | State |
|---|---|
| `<html dir>` | **Was missing** — hardcoded `lang="en"`, no direction. |
| i18n library | **None** (no next-intl / react-intl / i18next in `package.json`). |
| Translation catalogs | **None** (no `ar.json` / `locales/`). |
| UI strings | Hardcoded English inline across pages. |
| Dates / numbers | Pinned to `'en-US'` in `lib/cycomModels.ts`. |
| Backend locale | `locale` accepted on signup/demo, but no localized content pipeline audited. |

Conclusion: RTL/Arabic is **Missing**, not Partial — a feature to build, not a gap to patch.

## What this pass added (the foundation, not the feature)

- `components/LocaleDirection.tsx` — sets `document.documentElement.dir`/`lang`
  from the viewer's stored locale (`applyLocale('ar')` ⇒ `dir="rtl"`), persisted
  per browser. RTL locales: ar, he, fa, ur.
- Wired into `app/layout.tsx` (with `suppressHydrationWarning` on `<html>`).

Effect: switching locale to `ar` now flips the whole document to RTL. Flex/grid
layouts mirror automatically; **physical** utilities (`ml-`, `pr-`, `left-`) will
NOT mirror — that's the styling work below.

## Roadmap to real bilingual support (P1 mini-project)

1. **i18n library** — adopt `next-intl` (App Router-native). Locale in the URL or
   a cookie; message catalogs per namespace.
2. **String extraction** — wrap UI copy in `t('key')`; build `en.json` + `ar.json`.
   High-volume mechanical work → Haiku-tier per the model-selection guidance.
3. **Arabic translations** — native/professional review of ERP terminology
   (accounting, POS, HR terms are not machine-translatable safely).
4. **RTL-safe styling** — replace physical Tailwind utilities with logical ones
   (`ml`→`ms`, `pr`→`pe`, `left`→`start`, `text-left`→`text-start`); audit which
   icons/chevrons must flip and which must not (logos, media controls).
5. **Locale-aware formatting** — replace the hardcoded `'en-US'` in
   `lib/cycomModels.ts` with the active locale; offer Arabic-Indic numerals.
6. **Language toggle** — a control in the app shell calling `applyLocale`.
7. **Backend content** — localized emails, invoices/receipts (PDF), and API error
   messages via Django i18n + `Accept-Language`.

## Priority

P1 for the CyCom commercial launch in Arabic-speaking markets (JO/SA/AE). The
foundation here unblocks starting it; the string-extraction + translation pass is
the bulk of the effort and should be its own tracked workstream.
