# CyberCom SEO Strategy

**Program 3.10** — Search Engine Optimization Plan  
**Target Markets**: Middle East, MENA Region, Global Healthcare Tech

---

## Target Keyword Clusters

### Healthcare Platform SEO
| Keyword | Intent | Priority |
|---------|--------|----------|
| FHIR EMR system | Commercial | High |
| ICD-11 hospital management | Commercial | High |
| healthcare platform Saudi Arabia | Commercial | High |
| FHIR-native EHR | Commercial | High |
| clinical decision support system | Commercial | Medium |
| hospital information system | Commercial | High |
| نظام صحي FHIR | Commercial (AR) | High |
| نظام إدارة المستشفيات | Commercial (AR) | High |

### ERP SEO
| Keyword | Intent | Priority |
|---------|--------|----------|
| ERP system Middle East | Commercial | High |
| enterprise resource planning Saudi Arabia | Commercial | High |
| Arabic ERP system | Commercial | High |
| نظام تخطيط موارد المؤسسات | Commercial (AR) | High |

### Government SEO
| Keyword | Intent | Priority |
|---------|--------|----------|
| digital government platform | Commercial | High |
| citizen services platform | Commercial | Medium |
| government digital transformation | Informational | Medium |
| e-government solution | Commercial | High |

### AI & Platform SEO
| Keyword | Intent | Priority |
|---------|--------|----------|
| clinical AI platform | Commercial | High |
| OAuth 2.1 identity provider | Commercial | Medium |
| FHIR integration middleware | Commercial | High |

---

## Technical SEO Implementation

### URL Structure
```
www.cy-com.com/en/                          # Homepage (EN)
www.cy-com.com/ar/                          # Homepage (AR)
www.cy-com.com/en/products/cymed-hospital   # Product pages
www.cy-com.com/en/industries/healthcare     # Industry pages
```

### Hreflang Tags
```html
<link rel="alternate" hreflang="en" href="https://www.cy-com.com/en/" />
<link rel="alternate" hreflang="ar" href="https://www.cy-com.com/ar/" />
<link rel="alternate" hreflang="x-default" href="https://www.cy-com.com/en/" />
```

### Canonical URLs
All pages include self-referencing canonical URLs via `buildMetadata()`.

### Structured Data (JSON-LD)

**Homepage** — `Organization` schema:
- name, url, logo, description, sameAs (LinkedIn, Twitter)
- `contactPoint` (sales)
- `hasOfferCatalog` with SoftwareApplication entries

**Product Pages** — `SoftwareApplication` schema:
- name, applicationCategory, description, offers

**Industry Pages** — `Service` schema

### Core Web Vitals Targets
| Metric | Target | Implementation |
|--------|--------|----------------|
| LCP | < 2.5s | Next.js Image, font preloading |
| FID/INP | < 100ms | Server components, code splitting |
| CLS | < 0.1 | Image dimensions declared, no layout shifts |

### Performance Implementation
- `next/image` with WebP/AVIF, `sizes` attribute, `priority` on hero image
- Google Fonts with `display=swap` and preconnect
- Route-based code splitting (Next.js App Router)
- ISR cache: `revalidate: 300` on all API-driven pages
- Static generation for product/industry pages

---

## Content SEO

### Page Structure (each product page)
1. `<h1>` — Product name + tagline (primary keyword)
2. `<h2>` — "Key Features" section
3. `<h2>` — "Editions" section
4. `<h2>` — "Deployment Models" section
5. Schema.org `SoftwareApplication` markup
6. Internal links to related products and demo page

### Blog/Content Strategy (future)
- Healthcare digitalization thought leadership
- FHIR implementation guides
- ICD-11 adoption roadmap
- Government digital transformation case studies

---

## Arabic SEO

### RTL Requirements
- `dir="rtl"` on `<html>` for Arabic pages
- Noto Sans Arabic font for correct Arabic rendering
- Arabic-specific metadata (`locale="ar_SA"`)

### Arabic Keyword Optimization
All Arabic pages use the `messages/ar.json` translations with:
- Proper Arabic medical terminology
- Saudi-specific healthcare phrases
- Government and citizen service terms

---

## Analytics & Tracking

### Google Analytics 4
- Event: `demo_request_submit` (conversion goal)
- Event: `contact_form_submit`
- Event: `newsletter_subscribe`
- Event: `product_view` (product slug parameter)
- Event: `industry_view`

### Microsoft Clarity
- Session recording for UX analysis
- Heatmaps for CTA positioning optimization
- Loaded as async script to not impact performance

### CyData Integration
Custom analytics events pushed to CyData for:
- Industry interest tracking
- Product page engagement
- Demo request funnel analysis
- Geographic distribution of leads
