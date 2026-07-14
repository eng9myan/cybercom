"use client";

import Link from "next/link";
import { motion, useReducedMotion, AnimatePresence } from "framer-motion";
import { ArrowRight, ChevronRight } from "lucide-react";
import { type Locale } from "@/lib/i18n";
import { useState, useEffect, useRef } from "react";
import { useTranslations } from "next-intl";

interface HeroProps {
  locale: Locale;
}

const BADGE_ACCENTS = [
  { accent: "#34d399", slug: "CyMed" },
  { accent: "#ed6c00", slug: "CyShop" },
  { accent: "#60a5fa", slug: "CyCom ERP" },
] as const;

const BADGES = [
  "FHIR R4", "ICD-11", "SNOMED CT", "OIDC", "HIPAA Ready",
  "HL7 v2", "DICOM", "ISO 27001", "SOC 2 Type II", "GDPR",
  "OAuth 2.1", "Zero Trust", "PCI-DSS", "ZATCA", "WPS",
  "UAE FTA VAT", "Jordan SSC", "IFRS", "GAAP",
];

interface StatData { end: number; suffix: string; label: string; color: string; }

function useCountUp(end: number, duration: number, delay: number, started: boolean) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    if (!started) return;
    const t = setTimeout(() => {
      const t0 = performance.now();
      const tick = (now: number) => {
        const p = Math.min((now - t0) / duration, 1);
        setVal(end * (1 - Math.pow(1 - p, 3)));
        if (p < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    }, delay);
    return () => clearTimeout(t);
  }, [started, end, duration, delay]);
  return val;
}

function StatItem({ stat, delay, started }: { stat: StatData; delay: number; started: boolean }) {
  const v = useCountUp(stat.end, 1400, delay, started);
  const display = stat.end % 1 === 0 ? Math.round(v).toString() : v.toFixed(1);
  return (
    <div className="bg-white/[0.04] backdrop-blur-sm p-6 text-center hover:bg-white/[0.07] transition-colors duration-300">
      <div className="font-heading font-bold text-3xl lg:text-4xl mb-1 tabular-nums" style={{ color: stat.color }}>
        {display}{stat.suffix}
      </div>
      <div className="text-xs text-white/40 font-medium tracking-wide mt-0.5">{stat.label}</div>
    </div>
  );
}

export function Hero({ locale }: HeroProps) {
  const t = useTranslations("hero");
  const shouldReduce = useReducedMotion();
  const [wordIdx, setWordIdx] = useState(0);
  const [statsStarted, setStatsStarted] = useState(false);
  const statsRef = useRef<HTMLDivElement>(null);

  const CYCLING_WORDS = [
    { text: t("words.healthcare"), ...BADGE_ACCENTS[0] },
    { text: t("words.retail"),     ...BADGE_ACCENTS[1] },
    { text: t("words.enterprise"), ...BADGE_ACCENTS[2] },
  ];

  const HIGHLIGHTS = [
    { label: t("highlights.fhir"),      color: "#34d399" },
    { label: t("highlights.ai"),        color: "#a78bfa" },
    { label: t("highlights.inventory"), color: "#ed6c00" },
    { label: t("highlights.security"),  color: "#60a5fa" },
  ];

  const STATS: StatData[] = [
    { end: 3,    suffix: "",   label: t("stats.platformsLabel"), color: "#ed6c00" },
    { end: 14,   suffix: "+",  label: t("stats.erpLabel"),       color: "#60a5fa" },
    { end: 9,    suffix: "",   label: t("stats.clinicalLabel"),  color: "#34d399" },
    { end: 99.9, suffix: "%",  label: t("stats.uptimeLabel"),    color: "#a78bfa" },
  ];

  useEffect(() => {
    if (shouldReduce) return;
    const len = CYCLING_WORDS.length;
    const id = setInterval(() => setWordIdx(i => (i + 1) % len), 2800);
    return () => clearInterval(id);
  }, [shouldReduce, CYCLING_WORDS.length]);

  useEffect(() => {
    const el = statsRef.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      (entries) => { if (entries[0]?.isIntersecting) { setStatsStarted(true); obs.disconnect(); } },
      { threshold: 0.3 }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  const word = CYCLING_WORDS[wordIdx % CYCLING_WORDS.length]!;
  const doubled = [...BADGES, ...BADGES];

  const fade = (delay: number) => ({
    hidden: { opacity: 0, y: shouldReduce ? 0 : 28 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.7, delay, ease: [0.22, 1, 0.36, 1] as const } },
  });

  return (
    <section
      className="relative min-h-dvh flex flex-col items-center justify-center pt-16 overflow-hidden"
      aria-labelledby="hero-heading"
    >
      {/* ── Aurora background ──────────────────────────── */}
      <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
        {/* Primary blob — orange */}
        <div
          className="absolute -top-[25%] left-1/2 -translate-x-1/2 w-[110vw] h-[75vh] rounded-full"
          style={{
            background: "radial-gradient(ellipse, rgba(237,108,0,0.14) 0%, rgba(237,108,0,0.04) 45%, transparent 70%)",
            filter: "blur(80px)",
            animation: "aurora1 18s ease-in-out infinite",
          }}
        />
        {/* Cyan blob — left */}
        <div
          className="absolute top-[15%] -left-[15%] w-[55vw] h-[55vh] rounded-full"
          style={{
            background: "radial-gradient(ellipse, rgba(89,195,225,0.1) 0%, rgba(89,195,225,0.03) 50%, transparent 70%)",
            filter: "blur(90px)",
            animation: "aurora2 22s ease-in-out infinite",
          }}
        />
        {/* Violet blob — bottom-right */}
        <div
          className="absolute bottom-[5%] right-[0%] w-[45vw] h-[45vh] rounded-full"
          style={{
            background: "radial-gradient(ellipse, rgba(139,92,246,0.08) 0%, rgba(139,92,246,0.02) 50%, transparent 70%)",
            filter: "blur(70px)",
            animation: "aurora3 26s ease-in-out infinite",
          }}
        />

        {/* Dot grid */}
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: "radial-gradient(circle, rgba(255,255,255,0.6) 1px, transparent 1px)",
            backgroundSize: "40px 40px",
            opacity: 0.032,
          }}
        />

        {/* Vignettes */}
        <div className="absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-cy-black to-transparent" />
        <div className="absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-cy-black to-transparent" />
      </div>

      <div className="section-container relative z-10 text-center">

        {/* ── Eyebrow pill ───────────────────────────────── */}
        <motion.div
          variants={fade(0)} initial="hidden" animate="visible"
          className="inline-flex items-center gap-3 px-4 py-2 rounded-full border border-white/[0.09] bg-white/[0.04] backdrop-blur-md mb-10"
          style={{ boxShadow: "0 0 0 1px rgba(255,255,255,0.04), 0 4px 16px rgba(0,0,0,0.35)" }}
        >
          <span className="relative flex h-2 w-2 flex-shrink-0" aria-hidden="true">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cy-orange opacity-55" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-cy-orange" />
          </span>
          <span className="text-xs font-medium text-white/55 tracking-widest uppercase">
            {t("eyebrow")}
          </span>
        </motion.div>

        {/* ── Headline ───────────────────────────────────── */}
        <motion.h1
          id="hero-heading"
          variants={fade(0.08)} initial="hidden" animate="visible"
          className="font-heading font-semibold leading-[1.05] tracking-tight max-w-5xl mx-auto"
          style={{ fontSize: "clamp(2.6rem, 7vw, 5.5rem)" }}
        >
          <span className="block text-white/88">{t("headlinePrefix")}</span>

          {/* Cycling word */}
          <span
            className="relative block overflow-hidden"
            style={{ height: "1.12em", marginTop: "0.05em" }}
            aria-live="polite"
            aria-atomic="true"
          >
            <AnimatePresence mode="wait">
              <motion.span
                key={wordIdx}
                initial={{ y: shouldReduce ? 0 : "110%", opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: shouldReduce ? 0 : "-110%", opacity: 0 }}
                transition={{ duration: 0.48, ease: [0.22, 1, 0.36, 1] }}
                className="absolute inset-0 flex items-center justify-center"
                style={{
                  background: `linear-gradient(130deg, ${word.accent} 0%, ${word.accent}aa 100%)`,
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  backgroundClip: "text",
                }}
              >
                {word.text}
              </motion.span>
            </AnimatePresence>
          </span>
        </motion.h1>

        {/* ── Description ────────────────────────────────── */}
        <motion.p
          variants={fade(0.16)} initial="hidden" animate="visible"
          className="mt-7 text-lg sm:text-xl text-white/42 max-w-2xl mx-auto leading-relaxed font-light"
        >
          {t("description")}
        </motion.p>

        {/* ── CTAs ───────────────────────────────────────── */}
        <motion.div
          variants={fade(0.24)} initial="hidden" animate="visible"
          className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-10"
        >
          <Link href={`/${locale}/demo`} className="btn-primary-glow text-base px-8 py-3.5 group">
            {t("cta.demo")}
            <ArrowRight
              className="w-4 h-4 transition-transform duration-200 group-hover:translate-x-0.5 rtl:rotate-180"
              aria-hidden="true"
            />
          </Link>
          <Link href={`/${locale}/products`} className="btn-secondary text-base px-8 py-3.5 group">
            {t("cta.explore")}
            <ChevronRight
              className="w-4 h-4 transition-transform duration-200 group-hover:translate-x-0.5 rtl:rotate-180"
              aria-hidden="true"
            />
          </Link>
        </motion.div>

        {/* ── Feature dots ───────────────────────────────── */}
        <motion.div
          variants={fade(0.3)} initial="hidden" animate="visible"
          className="mt-10 flex flex-wrap justify-center gap-x-8 gap-y-2"
          aria-hidden="true"
        >
          {HIGHLIGHTS.map(h => (
            <span key={h.label} className="flex items-center gap-2 text-sm text-white/45">
              <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: h.color }} />
              {h.label}
            </span>
          ))}
        </motion.div>

        {/* ── Compliance marquee ─────────────────────────── */}
        <motion.div
          variants={fade(0.36)} initial="hidden" animate="visible"
          className="mt-12 relative overflow-hidden"
          aria-label="Compliance certifications and standards"
        >
          {/* Edge fades */}
          <div
            className="absolute left-0 top-0 bottom-0 w-24 z-10 pointer-events-none"
            style={{ background: "linear-gradient(to right, #0a0a0f, transparent)" }}
          />
          <div
            className="absolute right-0 top-0 bottom-0 w-24 z-10 pointer-events-none"
            style={{ background: "linear-gradient(to left, #0a0a0f, transparent)" }}
          />
          <div className="marquee-track" aria-hidden="true">
            {doubled.map((b, i) => (
              <span
                key={i}
                className="inline-flex items-center px-3 py-1.5 rounded-full border border-white/[0.07] bg-white/[0.03] text-xs font-medium text-white/45 flex-shrink-0"
              >
                {b}
              </span>
            ))}
          </div>
        </motion.div>

        {/* ── Stats ──────────────────────────────────────── */}
        <motion.div
          ref={statsRef}
          variants={fade(0.44)} initial="hidden" animate="visible"
          className="mt-16 grid grid-cols-2 lg:grid-cols-4 gap-px max-w-3xl mx-auto rounded-3xl overflow-hidden"
          style={{
            background: "rgba(255,255,255,0.055)",
            border: "1px solid rgba(255,255,255,0.07)",
            boxShadow: "0 0 0 1px rgba(255,255,255,0.04), 0 8px 40px rgba(0,0,0,0.45)",
          }}
          role="list"
          aria-label="Platform highlights"
        >
          {STATS.map((s, i) => (
            <div key={s.label} role="listitem">
              <StatItem stat={s} delay={i * 130} started={statsStarted} />
            </div>
          ))}
        </motion.div>
      </div>

      {/* ── Scroll cue ─────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0 }} animate={{ opacity: 1 }}
        transition={{ delay: 1.5, duration: 1 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
        aria-hidden="true"
      >
        <div
          className="w-px h-12"
          style={{ background: "linear-gradient(to bottom, transparent, rgba(255,255,255,0.18), transparent)" }}
        />
        <span className="text-[0.6rem] text-white/22 uppercase tracking-[0.25em]">Scroll</span>
      </motion.div>
    </section>
  );
}
