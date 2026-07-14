'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  ArrowRight, Sparkles, ShieldCheck, Cpu, Zap, BarChart3, Layers, Brain,
  ChevronRight, Globe, Check, Play
} from 'lucide-react';
import Logo from '@/components/brand/Logo';

const PARTNERS = ['VISA', 'STRIPE', 'AWS', 'PostgreSQL', 'Redis', 'CloudFlare', 'GitHub', 'Linear'];

const FEATURES = [
  { icon: Brain, title: 'AI Copilot for Sales', body: 'Conversational agent drafts quotes, scores leads, predicts churn — trained on your tenant data, isolated per workspace.', tone: 'orange' },
  { icon: BarChart3, title: 'Real-Time Analytics', body: 'Stream orders, inventory, and pipeline KPIs to a single sub-second dashboard. No batch jobs.', tone: 'blue' },
  { icon: Layers, title: 'Multi-Tenant Core', body: 'Row-level isolation, per-tenant secrets, RBAC, and audit log baked into the request pipeline.', tone: 'ink' },
  { icon: ShieldCheck, title: 'Compliance Ready', body: 'JWT auth, encrypted transport, immutable audit trail. Designed for SOC2 + GDPR controls.', tone: 'orange' },
  { icon: Zap, title: 'GraphQL + REST', body: 'One schema, two transports. REST for CRUD, GraphQL for nested queries — no extra services.', tone: 'blue' },
  { icon: Cpu, title: 'Edge-Ready', body: 'Containerized backend, standalone Next.js bundle, healthchecks, and CI image builds out of the box.', tone: 'ink' },
];

const METRICS = [
  { value: '99.95%', label: 'Uptime SLA' },
  { value: '<120ms', label: 'p95 API latency' },
  { value: '12k+', label: 'Tenants ready' },
  { value: '40+', label: 'AI workflows' },
];

const STEPS = [
  { n: '01', title: 'Provision tenant', body: 'Spin a new workspace in seconds — isolated DB schema, JWT keypair, default roles.' },
  { n: '02', title: 'Connect data', body: 'Sync products, customers, orders via REST/GraphQL or bulk import.' },
  { n: '03', title: 'Activate AI', body: 'Enable copilot, demand forecasting, churn alerts. Models trained on your tenant.' },
  { n: '04', title: 'Ship', body: 'One docker compose up — Postgres, Redis, backend, frontend. Or deploy each service standalone.' },
];

const PLANS = [
  { name: 'Starter', price: '19', blurb: 'For independent sellers getting set up.', features: ['1 tenant', '3 users', 'REST API', 'Basic AI copilot', 'Community support'], cta: 'Request Demo', featured: false },
  { name: 'Growth', price: '79', blurb: 'For teams scaling order volume and channels.', features: ['5 tenants', '25 users', 'GraphQL + REST', 'Full AI suite', 'Priority email support', 'SSO (Google/OIDC)'], cta: 'Request Demo', featured: true },
  { name: 'Enterprise', price: 'Custom', blurb: 'For multi-brand ops needing isolation + audit.', features: ['Unlimited tenants', 'Custom RBAC', 'Dedicated infra', 'SLA + DPA', 'Private model hosting'], cta: 'Talk to sales', featured: false },
];

export default function Landing() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <div className="relative min-h-screen overflow-x-clip text-[var(--color-ink)]">
      <header className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${scrolled ? 'bg-[#0a0a0f]/90 backdrop-blur-xl border-b border-[rgba(255,255,255,0.08)]' : 'bg-transparent'}`}>
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Logo />
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-[var(--color-ink-soft)]">
            <Link href="#features" className="hover:text-[var(--color-ink)] transition">Platform</Link>
            <Link href="#how" className="hover:text-[var(--color-ink)] transition">How it works</Link>
            <Link href="#pricing" className="hover:text-[var(--color-ink)] transition">Pricing</Link>
            <Link href="/industries" className="hover:text-[var(--color-ink)] transition">Industries</Link>
          </nav>
          <div className="flex items-center gap-2">
            <Link href="/login?demo=1" className="cy-btn cy-btn-ghost hidden sm:inline-flex text-[var(--color-brand-blue)] border-[rgba(89,195,225,0.3)] hover:bg-[rgba(89,195,225,0.06)]">Live Demo</Link>
            <Link href="/login" className="cy-btn cy-btn-ghost hidden sm:inline-flex">Sign in</Link>
            <Link href="/wizard" className="cy-btn cy-btn-primary">Start free <ArrowRight className="w-4 h-4" /></Link>
          </div>
        </div>
      </header>

      <section className="relative pt-32 pb-24 md:pt-40 md:pb-32">
        <div className="cy-mesh" />
        <div className="cy-grid" />
        <div className="relative max-w-7xl mx-auto px-6">
          <div className="cy-rise max-w-3xl">
            <span className="cy-pill"><Sparkles className="w-3.5 h-3.5" /> AI-native commerce OS · v1.0</span>
            <h1 className="mt-6 text-[clamp(2.5rem,6vw,4.75rem)] font-heading font-black leading-[1.02] tracking-tight">
              The commerce OS that <span className="cy-text-gradient">thinks</span> with your team.
            </h1>
            <p className="mt-6 text-lg md:text-xl text-[var(--color-ink-soft)] max-w-2xl leading-relaxed">
              Cyshop unifies your CRM, orders, inventory, and customer portal under one multi-tenant core —
              with an AI copilot that drafts quotes, forecasts demand, and flags churn before it happens.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link href="/login?demo=1" className="cy-btn cy-btn-primary bg-gradient-to-br from-[#59C3E1] to-[#0E7C9B] border-none shadow-[0_8px_20px_-8px_rgba(89,195,225,0.55)] hover:shadow-[0_12px_28px_-8px_rgba(89,195,225,0.7)] text-white">
                Launch Live Demo <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/wizard" className="cy-btn cy-btn-ghost">Start free trial</Link>
              <button className="cy-btn cy-btn-ghost"><Play className="w-4 h-4" /> Watch 2-min demo</button>
              <span className="inline-flex items-center gap-2 text-sm text-[var(--color-ink-muted)] ml-1">
                <span className="cy-blink" /> Live multi-tenant sandbox
              </span>
            </div>
          </div>

          <div className="relative mt-16 md:mt-20">
            <div className="cy-glass p-2 md:p-3 max-w-6xl mx-auto">
              <div className="rounded-[12px] bg-gradient-to-br from-[#0F1014] via-[#15171C] to-[#0F1014] p-6 md:p-8 overflow-hidden relative">
                <div className="flex items-center gap-2 mb-6">
                  <span className="w-3 h-3 rounded-full bg-[#FF5F57]" />
                  <span className="w-3 h-3 rounded-full bg-[#FEBC2E]" />
                  <span className="w-3 h-3 rounded-full bg-[#28C840]" />
                  <span className="ml-3 text-xs font-mono text-zinc-500">cyshop.app/app/sales-dashboard</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {METRICS.slice(0, 3).map((m) => (
                    <div key={m.label} className="rounded-xl bg-white/[0.04] border border-white/[0.08] p-5">
                      <div className="text-xs uppercase tracking-widest text-zinc-400">{m.label}</div>
                      <div className="mt-2 text-3xl font-heading font-black text-white">{m.value}</div>
                      <div className="mt-3 h-12 flex items-end gap-1">
                        {Array.from({ length: 22 }).map((_, i) => (
                          <div key={i} className="flex-1 rounded-sm"
                            style={{ height: `${30 + Math.abs(Math.sin(i * 0.7)) * 70}%`, background: i % 4 === 0 ? '#ED6C00' : 'rgba(89,195,225,.6)' }} />
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-5 rounded-xl bg-white/[0.04] border border-white/[0.08] p-5 flex items-start gap-4">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#ED6C00] to-[#FF8A2A] flex items-center justify-center shrink-0">
                    <Sparkles className="w-5 h-5 text-white" />
                  </div>
                  <div className="text-sm text-zinc-300 leading-relaxed">
                    <span className="text-zinc-500">AI Copilot · </span>
                    Pipeline at <span className="text-white font-semibold">$847k</span>. Two enterprise deals
                    likely to slip past Q3 — recommend follow-up sequences for{' '}
                    <span className="text-[#59C3E1] font-semibold">Acme</span> and{' '}
                    <span className="text-[#59C3E1] font-semibold">Initech</span>.
                  </div>
                </div>
              </div>
            </div>
            <div className="absolute -top-10 -left-10 w-40 h-40 rounded-full bg-[#ED6C00]/20 blur-3xl pointer-events-none" />
            <div className="absolute -bottom-10 -right-10 w-56 h-56 rounded-full bg-[#59C3E1]/25 blur-3xl pointer-events-none" />
          </div>
        </div>
      </section>

      <section className="py-10 border-y border-[rgba(255,255,255,.08)] bg-[var(--color-surface)] overflow-hidden">
        <div className="max-w-7xl mx-auto px-6">
          <p className="text-xs uppercase tracking-[0.25em] text-[var(--color-ink-muted)] text-center mb-6">
            Trusted infrastructure · production-ready stack
          </p>
          <div className="relative overflow-hidden mask-fade">
            <div className="cy-marquee">
              {[...PARTNERS, ...PARTNERS].map((p, i) => (
                <span key={i} className="text-xl md:text-2xl font-heading font-black text-[var(--color-ink-muted)] tracking-wider shrink-0">{p}</span>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section id="features" className="py-24 md:py-32">
        <div className="max-w-7xl mx-auto px-6">
          <div className="max-w-2xl">
            <span className="cy-pill cy-pill-orange"><Brain className="w-3.5 h-3.5" /> Built with AI from the core</span>
            <h2 className="mt-5 text-4xl md:text-5xl font-heading font-black leading-tight">
              An OS that ships features, <br /> not just dashboards.
            </h2>
            <p className="mt-4 text-lg text-[var(--color-ink-soft)]">
              Every module — sales, orders, inventory, notifications — is wired to a tenant-aware AI layer.
              You don't bolt AI on. It's the first-class citizen.
            </p>
          </div>
          <div className="mt-14 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map((f) => (
              <article key={f.title} className="cy-card p-6 group">
                <div className="w-11 h-11 rounded-xl flex items-center justify-center mb-5"
                  style={{
                    background: f.tone === 'orange' ? 'rgba(237,108,0,.10)' : f.tone === 'blue' ? 'rgba(89,195,225,.15)' : 'rgba(17,17,17,.06)',
                    color:      f.tone === 'orange' ? '#ED6C00' : f.tone === 'blue' ? '#0E7C9B' : '#1A1A1A',
                  }}>
                  <f.icon className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-heading font-bold">{f.title}</h3>
                <p className="mt-2 text-sm text-[var(--color-ink-soft)] leading-relaxed">{f.body}</p>
                <div className="mt-5 flex items-center gap-1.5 text-sm font-semibold text-[var(--color-ink)] opacity-0 group-hover:opacity-100 transition">
                  Learn more <ChevronRight className="w-4 h-4" />
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="relative py-20">
        <div className="max-w-7xl mx-auto px-6">
          <div className="relative rounded-[28px] overflow-hidden p-10 md:p-16 bg-[var(--color-brand-ink)] text-white">
            <div className="absolute inset-0 opacity-60 pointer-events-none"
              style={{ background: 'radial-gradient(40rem 30rem at 100% 0%, rgba(237,108,0,.45), transparent 60%), radial-gradient(40rem 30rem at 0% 100%, rgba(89,195,225,.35), transparent 60%)' }} />
            <div className="relative grid grid-cols-2 md:grid-cols-4 gap-8">
              {METRICS.map((m) => (
                <div key={m.label}>
                  <div className="text-4xl md:text-5xl font-heading font-black cy-text-gradient">{m.value}</div>
                  <div className="mt-2 text-sm uppercase tracking-widest text-white/70">{m.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section id="how" className="py-24 md:py-32 bg-[var(--color-surface)]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-14">
            <div className="max-w-xl">
              <span className="cy-pill">How it works</span>
              <h2 className="mt-5 text-4xl md:text-5xl font-heading font-black leading-tight">
                From signup to ship — <br /> in under an afternoon.
              </h2>
            </div>
            <Link href="/wizard" className="cy-btn cy-btn-dark self-start md:self-end">
              Launch the wizard <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <ol className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            {STEPS.map((s) => (
              <li key={s.n} className="cy-card p-6 relative">
                <div className="font-mono text-sm text-[var(--color-ink-muted)]">{s.n}</div>
                <div className="mt-3 text-lg font-heading font-bold">{s.title}</div>
                <p className="mt-2 text-sm text-[var(--color-ink-soft)] leading-relaxed">{s.body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section id="pricing" className="py-24 md:py-32">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto">
            <span className="cy-pill">Pricing</span>
            <h2 className="mt-5 text-4xl md:text-5xl font-heading font-black leading-tight">Pay for tenants, not seats.</h2>
            <p className="mt-4 text-lg text-[var(--color-ink-soft)]">
              Transparent monthly pricing. Cancel anytime. AI usage included in every plan.
            </p>
          </div>
          <div className="mt-14 grid grid-cols-1 md:grid-cols-3 gap-6">
            {PLANS.map((p) => (
              <div key={p.name} className={`relative rounded-[20px] p-8 border transition-all ${p.featured ? 'bg-gradient-to-br from-[#1a1a2e] to-[#0f0f1a] text-white border-[rgba(237,108,0,.3)] shadow-[0_20px_60px_-20px_rgba(237,108,0,.5)]' : 'bg-[rgba(255,255,255,.04)] border-[rgba(255,255,255,.08)] hover:border-[rgba(255,255,255,.2)]'}`}>
                {p.featured && <span className="absolute -top-3 left-8 cy-pill cy-pill-orange">Most popular</span>}
                <div className={`text-sm font-bold uppercase tracking-widest ${p.featured ? 'text-white/70' : 'text-[var(--color-ink-soft)]'}`}>{p.name}</div>
                <div className="mt-4 flex items-baseline gap-1">
                  <span className="text-5xl font-heading font-black">{p.price === 'Custom' ? p.price : `$${p.price}`}</span>
                  {p.price !== 'Custom' && <span className={`text-sm ${p.featured ? 'text-white/60' : 'text-[var(--color-ink-muted)]'}`}>/ tenant / mo</span>}
                </div>
                <p className={`mt-3 text-sm ${p.featured ? 'text-white/70' : 'text-[var(--color-ink-soft)]'}`}>{p.blurb}</p>
                <ul className="mt-6 space-y-3 text-sm">
                  {p.features.map((feat) => (
                    <li key={feat} className="flex items-start gap-2">
                      <Check className={`w-4 h-4 mt-0.5 shrink-0 ${p.featured ? 'text-[#59C3E1]' : 'text-[#ED6C00]'}`} />
                      <span>{feat}</span>
                    </li>
                  ))}
                </ul>
                <Link href={p.name === 'Enterprise' ? '/contact' : '/wizard'} className={`mt-8 cy-btn w-full ${p.featured ? 'cy-btn-primary' : 'cy-btn-ghost'}`}>{p.cta}</Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-24">
        <div className="max-w-5xl mx-auto px-6">
          <div className="cy-glass p-12 md:p-16 text-center relative overflow-hidden">
            <div className="absolute -top-20 -left-20 w-72 h-72 rounded-full bg-[#ED6C00]/20 blur-3xl" />
            <div className="absolute -bottom-20 -right-20 w-72 h-72 rounded-full bg-[#59C3E1]/25 blur-3xl" />
            <div className="relative">
              <h2 className="text-4xl md:text-5xl font-heading font-black leading-tight">
                Ship the commerce stack <br /> your competitors wish they had.
              </h2>
              <p className="mt-4 text-lg text-[var(--color-ink-soft)] max-w-xl mx-auto">
                14-day free trial. No credit card. Real AI on real data — your data, isolated, encrypted.
              </p>
              <div className="mt-8 flex flex-wrap justify-center gap-3">
                <Link href="/login?demo=1" className="cy-btn cy-btn-primary bg-gradient-to-br from-[#59C3E1] to-[#0E7C9B] border-none shadow-[0_8px_20px_-8px_rgba(89,195,225,0.55)] hover:shadow-[0_12px_28px_-8px_rgba(89,195,225,0.7)] text-white">
                  Launch Live Demo <ArrowRight className="w-4 h-4" />
                </Link>
                <Link href="/wizard" className="cy-btn cy-btn-ghost">Start Free Trial</Link>
                <Link href="/contact" className="cy-btn cy-btn-ghost">Talk to sales</Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t border-[var(--color-line)] py-12">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between gap-8">
          <div>
            <Logo />
            <p className="mt-3 text-sm text-[var(--color-ink-muted)] max-w-xs">
              The AI-native commerce OS. Multi-tenant. Open core. Production-ready.
            </p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-sm">
            {[
              { h: 'Product', items: ['Platform', 'Pricing', 'Industries', 'Roadmap'] },
              { h: 'Developers', items: ['Docs', 'API', 'GraphQL', 'GitHub'] },
              { h: 'Company', items: ['About', 'Customers', 'Careers', 'Contact'] },
              { h: 'Legal', items: ['Privacy', 'Terms', 'DPA', 'Security'] },
            ].map((col) => (
              <div key={col.h}>
                <div className="font-heading font-bold mb-3">{col.h}</div>
                <ul className="space-y-2 text-[var(--color-ink-soft)]">
                  {col.items.map((i) => <li key={i}><a className="hover:text-[var(--color-ink)] transition" href="#">{i}</a></li>)}
                </ul>
              </div>
            ))}
          </div>
        </div>
        <div className="cy-divider my-8" />
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between gap-4 text-xs text-[var(--color-ink-muted)]">
          <span>© {new Date().getFullYear()} Cyshop · A CyberCom company</span>
          <span className="inline-flex items-center gap-1.5"><Globe className="w-3.5 h-3.5" /> EN · Built for global commerce</span>
        </div>
      </footer>

      <style jsx>{`
        .mask-fade { mask-image: linear-gradient(90deg, transparent, #000 8%, #000 92%, transparent); }
      `}</style>
    </div>
  );
}
