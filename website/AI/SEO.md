# SEO Reference

## SEO Architecture

SEO is implemented via `apps/web/lib/metadata.ts`.

```typescript
// Always use buildMetadata() for every page
export async function generateMetadata({ params }): Promise<Metadata> {
  const { locale } = await params;
  return buildMetadata({
    title: "Page Title — CyberCom",
    description: "150-160 char description",
    path: "/page-path",
    locale,
  });
}
```

---

## Meta Tag Requirements (Every Page)

| Tag | Requirement |
|-----|------------|
| `<title>` | Unique per page, 50–60 chars, includes product/company name |
| `description` | 140–160 chars, natural language, includes primary keyword |
| `og:title` | Same as title or variant |
| `og:description` | Same as meta description |
| `og:image` | 1200x630px, product/brand image |
| `og:url` | Canonical URL |
| `twitter:card` | `summary_large_image` |
| `canonical` | Self-referencing canonical URL |
| `hreflang` | `en` and `ar` alternates on every page |

---

## Structured Data (JSON-LD)

### Homepage
```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "CyberCom Revolution",
  "url": "https://www.cy-com.com",
  "logo": "https://www.cy-com.com/images/logo.png",
  "description": "...",
  "sameAs": ["LinkedIn URL", "GitHub URL"]
}
```

### Product Pages
```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "CyMed Hospital",
  "applicationCategory": "Healthcare Software",
  "operatingSystem": "Web, iOS, Android",
  "offers": {"@type": "Offer", "availability": "https://schema.org/InStock"}
}
```

### Contact Page
```json
{
  "@context": "https://schema.org",
  "@type": "ContactPage"
}
```

---

## Target Keywords

### Primary (homepage)

English: `healthcare management system`, `hospital information system`, `EHR software`, `FHIR platform`, `ICD-11 software`, `enterprise health platform`, `healthcare ERP`, `clinic management system`, `laboratory information system`, `radiology information system`

Arabic: `نظام إدارة المستشفيات`, `نظام معلومات المستشفى`, `برنامج السجلات الطبية`, `نظام إدارة العيادات`, `برنامج المختبرات`

### Product-Specific Keywords

| Product | Primary Keywords |
|---------|----------------|
| CyMed Hospital | hospital information system, HIS, inpatient management, ADT system |
| CyMed Clinic | clinic management system, outpatient EHR, appointment scheduling |
| CyMed Laboratory | LIS, laboratory information system, lab management |
| CyMed Imaging | RIS, radiology information system, PACS, DICOM |
| CyMed Pharmacy | pharmacy management system, dispensing software, drug interaction |
| CyMed Patient Portal | patient portal, patient engagement, PHR |
| CyMed Provider Portal | clinical workflow, provider portal, EHR |
| CyMed RCM | revenue cycle management, medical billing, claims management |
| CyMed Population Health | population health management, care management, analytics |
| CyCom ERP | enterprise ERP, ERP software, business management |
| CyGov | government software, digital government, e-government |

---

## URL Structure

- English: `cy-com.com/en/products/cymed-hospital`
- Arabic: `cy-com.com/ar/products/cymed-hospital`
- No trailing slashes
- All lowercase with hyphens
- Include product name in URL

---

## Sitemap

Auto-generate sitemap via `next-sitemap` or App Router `sitemap.ts`.

Include:
- All product pages (en + ar)
- All industry pages (en + ar)
- Homepage (en + ar)
- About, Contact, Partners, Demo (en + ar)

Exclude: `/admin/`, `/api/`, `/_next/`

---

## Robots.txt

```
User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/

Sitemap: https://www.cy-com.com/sitemap.xml
```

---

## Performance (Core Web Vitals affect SEO)

- LCP < 2.5s — use `next/image` with priority on hero images
- CLS < 0.1 — always set image dimensions, avoid dynamic content shifts
- INP < 200ms — minimize JS bundle size, use dynamic imports for heavy components
- Run `next build` and check bundle analyzer before release

---

## hreflang Implementation

In `apps/web/app/[locale]/layout.tsx`:

```tsx
<link rel="alternate" hrefLang="en" href="https://www.cy-com.com/en/..." />
<link rel="alternate" hrefLang="ar" href="https://www.cy-com.com/ar/..." />
<link rel="alternate" hrefLang="x-default" href="https://www.cy-com.com/en/..." />
```
