# CyberCom Design System

**Program 3.10** — Design Language Reference

---

## Philosophy

CyberCom's design language is **Liquid Glass on Dark** — a premium enterprise aesthetic inspired by OpenAI, Stripe, Vercel, and Palantir. Every visual decision reinforces trust, intelligence, and global-scale ambition.

---

## Design Tokens

### Colors

```css
/* Brand */
--cy-black: #0a0a0f;          /* Page background */
--cy-dark: #0f0f1a;           /* Section backgrounds */
--cy-navy: #0d1117;           /* Alt dark */
--cy-slate: #1e293b;          /* Elevated surfaces */

/* Accent */
--cy-orange: #ed6c00;         /* Primary CTA */
--cy-orange-light: #f59332;   /* Hover state */
--cy-orange-dim: rgba(237,108,0,0.13);  /* Tinted bg */
--cy-cyan: #59c3e1;           /* Secondary accent */
--cy-cyan-light: #7dd3ea;     /* Hover */
--cy-cyan-dim: rgba(89,195,225,0.09);  /* Tinted bg */

/* Glass */
--cy-glass-bg: rgba(255,255,255,0.04);
--cy-glass-bg-hover: rgba(255,255,255,0.08);
--cy-glass-border: rgba(255,255,255,0.08);

/* Text scale */
--cy-white: #ffffff;
--cy-gray-100: #f1f5f9;
--cy-gray-200: #e2e8f0;
--cy-gray-400: #94a3b8;
--cy-gray-600: #475569;
```

### Typography

| Role | Font | Weight | Usage |
|------|------|--------|-------|
| Display | Lexend | 700 | Hero headlines |
| Heading | Lexend | 600 | Section titles, product names |
| Label | Lexend | 500 | Navigation, badges, CTAs |
| Body | Source Sans 3 | 400 | Paragraphs, descriptions |
| Caption | Source Sans 3 | 400 | Helper text, metadata |
| Code | JetBrains Mono | 400/500 | Code blocks, technical values |
| Arabic | Noto Sans Arabic | 400/600 | RTL content |

**Type Scale:**

| Name | Size | Line Height | Usage |
|------|------|-------------|-------|
| `text-8xl` | 6rem | 6.5rem | Hero (desktop) |
| `text-7xl` | 4.5rem | 5rem | Hero (mobile) |
| `text-5xl` | 3rem | 3.5rem | Page titles |
| `text-4xl` | 2.25rem | 2.75rem | Section headings |
| `text-2xl` | 1.5rem | 2rem | Card headings |
| `text-xl` | 1.25rem | 1.875rem | Sub-headings |
| `text-base` | 1rem | 1.625rem | Body text |
| `text-sm` | 0.875rem | 1.375rem | Secondary text |
| `text-xs` | 0.75rem | 1.125rem | Labels, captions |
| `text-2xs` | 0.625rem | 1rem | Tags, metadata |

### Spacing

Uses 4pt/8dp incremental system. Key values:

| Token | Value | Usage |
|-------|-------|-------|
| `p-3` | 12px | Compact padding |
| `p-4` | 16px | Default card padding |
| `p-6` | 24px | Card padding |
| `p-8` | 32px | Section padding |
| `gap-4` | 16px | Default grid gap |
| `gap-6` | 24px | Card grid gap |

### Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `rounded-lg` | 8px | Buttons, inputs, small elements |
| `rounded-xl` | 12px | Cards, form elements |
| `rounded-2xl` | 16px | Large cards, sections |
| `rounded-full` | 9999px | Badges, avatars, pills |

---

## Component Patterns

### Glass Card

```html
<div class="glass-card p-6 rounded-2xl">
  <!-- content -->
</div>
```

**CSS**:
```css
.glass-card {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  backdrop-filter: blur(12px);
  border-radius: 1rem;
  box-shadow:
    0 0 0 1px rgba(255,255,255,0.06),
    0 8px 32px rgba(0,0,0,0.4);
  transition: box-shadow 0.25s ease, border-color 0.25s ease;
}

.glass-card:hover {
  background: rgba(255,255,255,0.08);
  border-color: rgba(255,255,255,0.12);
  box-shadow:
    0 0 0 1px rgba(255,255,255,0.12),
    0 16px 48px rgba(0,0,0,0.5);
}
```

### Button Variants

**Primary (Orange CTA)**:
```html
<button class="btn-primary">Request Demo</button>
```

**Secondary (Glass)**:
```html
<button class="btn-secondary">Learn More</button>
```

**Ghost**:
```html
<button class="btn-ghost">Cancel</button>
```

### Form Input

```html
<div>
  <label for="email" class="form-label">
    Email <span aria-hidden="true">*</span>
  </label>
  <input
    id="email"
    type="email"
    class="form-input"
    placeholder="you@company.com"
    required
    aria-required="true"
  />
</div>
```

### Gradient Text

```html
<span class="text-gradient">Intelligent Platforms</span>
```

### Glow Orb (Decorative Background)

```html
<div
  class="glow-orb w-[600px] h-[600px] -top-32 left-1/2 -translate-x-1/2 bg-cy-orange/8"
  aria-hidden="true"
/>
```

---

## Animation System

| Name | Duration | Easing | Usage |
|------|----------|--------|-------|
| `fade-in` | 500ms | ease-out | Content appearance |
| `fade-up` | 600ms | cubic [0.22, 1, 0.36, 1] | Section entry |
| `slide-in` | 400ms | ease-out | Panel entry |
| `glow-pulse` | 3s | ease-in-out infinite | Orb decorations |
| `float` | 6s | ease-in-out infinite | Floating elements |

**Framer Motion defaults**:
```typescript
const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] } },
};
```

All animations respect `prefers-reduced-motion` via `useReducedMotion()` hook.

---

## Accessibility Standards

Minimum WCAG 2.1 AA compliance:

1. **Color contrast**: All text meets 4.5:1 minimum
2. **Focus rings**: 2px orange ring on all interactive elements
3. **Skip links**: Skip to main content on all pages
4. **Alt text**: All meaningful images have descriptive alt text
5. **ARIA labels**: All icon-only buttons have `aria-label`
6. **Heading hierarchy**: Sequential h1→h6, no level skipping
7. **Form labels**: Visible `<label>` for every form input
8. **Error messages**: `role="alert"` and `aria-live` for dynamic errors
9. **Touch targets**: Minimum 44×44px on mobile
10. **Keyboard navigation**: Full tab order, predictable focus management

---

## Product Brand Colors

Each CyberCom product has a distinct accent color:

| Product | Color | Tailwind Class |
|---------|-------|----------------|
| CyMed | Emerald | `text-emerald-400` |
| CyCom | Blue | `text-blue-400` |
| CyGov | Amber | `text-amber-400` |
| CyIdentity | Violet | `text-violet-400` |
| CyIntegrationHub | Cyan | `text-cyan-400` |
| CyAI | Pink | `text-pink-400` |
| CyData | Teal | `text-teal-400` |
| CyConnect | Orange | `text-orange-400` |
| CyCitizen | Indigo | `text-indigo-400` |
