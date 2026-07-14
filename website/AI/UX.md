# UX Standards

## Design Principles

1. **Clarity over cleverness** — enterprise buyers evaluate on trust, not cleverness
2. **Information hierarchy** — most important content visible without scrolling
3. **Consistent patterns** — same interaction patterns across all pages
4. **Performance is UX** — slow page = lost lead
5. **Accessibility is non-negotiable** — WCAG 2.1 AA minimum

---

## Layout System

### Page Structure

```
<Header>         Fixed nav, logo, primary nav links, language toggle, CTA button
<main>
  <HeroSection>  Full-width, large headline, subheadline, primary CTA
  <Section ...>  Alternating sections with consistent padding
  <CTASection>   Demo request at bottom of every key page
</main>
<Footer>         Links, legal, social, language toggle
```

### Grid

- Mobile: 1 column
- Tablet (768px+): 2 columns
- Desktop (1280px+): 3–4 columns
- Max content width: 1280px (7xl) with horizontal padding

### Spacing

- Section vertical padding: `py-20` (5rem) on desktop, `py-12` on mobile
- Card padding: `p-6` (24px)
- Component gap: `gap-6` or `gap-8`

---

## Navigation

### Header
- Logo left
- Primary nav links center
- Language toggle (EN / AR)
- "Request Demo" CTA button right
- Mobile: hamburger menu

### Primary Nav Links
- Products
- Industries
- About
- Partners
- Contact

### Language Toggle
- Switch between `en` and `ar` with same-path redirect
- RTL layout on Arabic selection

---

## Product Cards

Standard product card pattern:

```tsx
<div className="bg-slate-800/50 border border-{color}-500/20 rounded-xl p-6 hover:border-{color}-500/50 transition-colors">
  <div className={`text-{color}-400 mb-4`}>
    <Icon />
  </div>
  <h3 className="text-white font-semibold text-lg mb-2">{product.name}</h3>
  <p className="text-slate-400 text-sm">{product.description}</p>
  <Link href={`/products/${product.slug}`} className={`text-{color}-400 mt-4 flex items-center gap-1`}>
    Learn more <ArrowRight size={14} />
  </Link>
</div>
```

---

## Forms (Contact, Demo Request, Partner Application)

```tsx
<form>
  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
    <FormField label="Name" required />
    <FormField label="Email" type="email" required />
    <FormField label="Company" required />
    <FormField label="Phone" type="tel" />
  </div>
  <FormField label="Message" multiline />
  <ConsentCheckbox label="I agree to the Privacy Policy" required />
  <SubmitButton>Submit</SubmitButton>
</form>
```

Form requirements:
- Client-side validation before submit
- Loading state on submit button
- Success state with confirmation message
- Error state with specific field errors from API
- GDPR consent checkbox on all lead forms

---

## Accessibility

### Requirements (WCAG 2.1 AA)

| Item | Requirement |
|------|------------|
| Color contrast | 4.5:1 for normal text, 3:1 for large text |
| Focus visible | All interactive elements have visible focus ring |
| Alt text | All images have descriptive alt text |
| Heading hierarchy | h1 → h2 → h3 in correct order |
| Link text | Descriptive (not "click here") |
| Form labels | All inputs have associated labels |
| ARIA | Use semantic HTML first, ARIA only when necessary |
| Keyboard nav | All interactions accessible via keyboard |

### RTL Accessibility
- `dir="rtl"` on root when Arabic
- Icons that indicate direction (arrows) flip with RTL
- Text alignment follows locale direction
- Number formatting: Arabic locale uses Eastern Arabic numerals where appropriate

---

## Interactive States

Every interactive element must have:
- `default` — base state
- `hover` — visual feedback (color/brightness change)
- `focus` — visible focus ring (accessibility)
- `active` — pressed state
- `disabled` — reduced opacity, cursor-not-allowed

---

## Animation & Motion

- Keep animations subtle and purposeful
- Fade-in on scroll for section reveals (`opacity-0 → opacity-100`)
- Transition duration: 150–300ms max
- No animation on reduced-motion preference (`@media (prefers-reduced-motion: reduce)`)
- No auto-playing video without user interaction

---

## Mobile Experience

- All pages fully functional on 375px (iPhone SE)
- Touch targets minimum 44x44px
- No horizontal scroll on any page
- Hamburger nav on mobile < 768px
- Card grids collapse to single column on mobile
- Forms stack vertically on mobile

---

## Error States

```tsx
// API error
<div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4">
  <p className="text-red-400">{errorMessage}</p>
</div>

// Success
<div className="bg-emerald-900/20 border border-emerald-500/30 rounded-lg p-4">
  <p className="text-emerald-400">{successMessage}</p>
</div>

// Loading
<div className="animate-pulse bg-slate-700 rounded h-4 w-full" />
```

---

## What NOT to Do

- Do not use light backgrounds (off-white, light gray) — dark palette only
- Do not use more than 2 font weights on a component
- Do not use custom cursor styles
- Do not use parallax effects
- Do not render content on hover-only interactions (mobile users cannot hover)
- Do not auto-advance carousels
- Do not open links in new tabs without warning (accessibility)
- Do not use lorem ipsum — all placeholder text must be real content
