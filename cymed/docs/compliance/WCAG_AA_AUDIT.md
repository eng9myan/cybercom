# WCAG 2.1 AA Accessibility Conformance — CyMed

## Scope
- Patient App (Flutter + PWA)
- Provider portal (web templates)
- Dashboard (web templates)
- FHIR / API docs (auto-generated)

## Principles

### Perceivable
| SC | Status | Notes |
|---|---|---|
| 1.1.1 Non-text content | ✅ | All icons have semantic labels; images have alt |
| 1.3.1 Info & relationships | ✅ | Semantic HTML in templates; Flutter Semantics widget |
| 1.4.3 Contrast (min AA) | ⚠ | Brand primary #0062CC on white passes AA large only — brand refresh pending |
| 1.4.4 Resize text 200% | ✅ | Flutter MediaQuery.textScaleFactor honoured |
| 1.4.10 Reflow | ✅ | Responsive layout |
| 1.4.11 Non-text contrast | ✅ | Icon strokes ≥ 3:1 |

### Operable
| SC | Status | Notes |
|---|---|---|
| 2.1.1 Keyboard | ✅ | Web templates all keyboard-navigable |
| 2.1.4 Character shortcuts | ✅ | Configurable in accessibility settings |
| 2.2.1 Timing adjustable | ⚠ | Session timeout warning w/ extend — build in Flutter |
| 2.3.1 Three flashes | ✅ | No flashing content |
| 2.4.3 Focus order | ✅ | Logical DOM order |
| 2.4.7 Focus visible | ✅ | 3px orange outline on focus |
| 2.5.3 Label in name | ✅ | Screen-reader labels match visible text |

### Understandable
| SC | Status | Notes |
|---|---|---|
| 3.1.1 Language of page | ✅ | `lang="ar"` / `lang="en"` at root; `dir="rtl"` when Arabic |
| 3.2.1 On focus | ✅ | No context change on focus |
| 3.3.1 Error identification | ✅ | Errors described textually, colour redundant |
| 3.3.2 Labels | ✅ | Every form input labelled |
| 3.3.3 Error suggestion | ✅ | Contextual help on failed input |

### Robust
| SC | Status | Notes |
|---|---|---|
| 4.1.2 Name, role, value | ✅ | Semantic widgets throughout |
| 4.1.3 Status messages | ⚠ | ARIA live regions in provider portal — Flutter has SemanticsService.announce |

## Audit tooling

- axe-core CI check on every PR (web templates).
- Flutter `flutter_test` accessibility_guideline tests.
- Manual keyboard + screen-reader (NVDA · VoiceOver · TalkBack) pass quarterly.

## Remediation queue

1. Fix contrast fail on primary CTAs — add darker fallback variant.
2. Build session-timeout warning modal.
3. Wire ARIA live regions in provider portal notifications.

## External audit
- Firm: Level Access or Deque.
- Cadence: annually.
- Report shared with client tenants + regulators.
