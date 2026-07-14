"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";

interface Stat {
  value: number;
  suffix: string;
  prefix?: string;
  label: string;
  color: string;
}

const STATS: Stat[] = [
  { value: 18,   suffix: "",   label: "ERP Modules",         color: "#60a5fa" },
  { value: 7,    suffix: "",   label: "Integrated Products",  color: "#34d399" },
  { value: 99.9, suffix: "%",  label: "Uptime SLA",           color: "#a78bfa" },
  { value: 38,   suffix: "+",  label: "Live Customers",       color: "#ed6c00" },
  { value: 5,    suffix: "+",  label: "GCC Markets",          color: "#f472b6" },
  { value: 14,   suffix: " days", label: "Free Trial",        color: "#59c3e1" },
];

const CERTS = [
  "FHIR R4 Certified",
  "ICD-11 Ready",
  "HIPAA Compliant",
  "ISO 27001",
  "SOC 2 Type II",
  "ZATCA e-Invoice",
  "HL7 v2 + v3",
  "DICOM PACS",
  "GDPR Ready",
  "OAuth 2.1",
  "Zero Trust",
  "PCI-DSS",
  "WPS Jordan",
  "UAE FTA VAT",
  "IFRS + GAAP",
];

function useCountUp(end: number, duration = 1600, delay = 0, started = false) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    if (!started) return;
    const timer = setTimeout(() => {
      const t0 = performance.now();
      const tick = (now: number) => {
        const p = Math.min((now - t0) / duration, 1);
        const eased = 1 - Math.pow(1 - p, 3);
        setVal(end * eased);
        if (p < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    }, delay);
    return () => clearTimeout(timer);
  }, [started, end, duration, delay]);
  return val;
}

function StatCounter({ stat, delay, started }: { stat: Stat; delay: number; started: boolean }) {
  const raw = useCountUp(stat.value, 1600, delay, started);
  const display = stat.value % 1 !== 0 ? raw.toFixed(1) : Math.round(raw).toString();

  return (
    <div className="group text-center py-6 px-4 relative">
      <div
        className="text-4xl lg:text-5xl font-heading font-bold tabular-nums mb-1 transition-transform duration-300 group-hover:scale-105"
        style={{ color: stat.color }}
      >
        {stat.prefix ?? ""}{display}{stat.suffix}
      </div>
      <div className="text-xs font-medium uppercase tracking-wider text-white/40">
        {stat.label}
      </div>
      <div
        className="absolute inset-x-0 bottom-0 h-0.5 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
        style={{ background: `linear-gradient(to right, transparent, ${stat.color}60, transparent)` }}
      />
    </div>
  );
}

export function StatsBand() {
  const shouldReduce = useReducedMotion();
  const ref = useRef<HTMLDivElement>(null);
  const [started, setStarted] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          setStarted(true);
          obs.disconnect();
        }
      },
      { threshold: 0.2 }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  const doubled = [...CERTS, ...CERTS];

  return (
    <section
      className="relative py-20 overflow-hidden"
      aria-label="Platform statistics"
    >
      {/* bg gradient */}
      <div
        className="absolute inset-0 pointer-events-none"
        aria-hidden="true"
        style={{
          background: "linear-gradient(180deg, transparent 0%, rgba(89,195,225,0.03) 50%, transparent 100%)",
        }}
      />

      <div className="section-container">
        {/* Section label */}
        <motion.div
          initial={{ opacity: 0, y: shouldReduce ? 0 : 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <p className="text-xs font-semibold uppercase tracking-widest text-cy-orange mb-2">
            By the Numbers
          </p>
          <h2 className="text-2xl lg:text-3xl font-heading font-semibold text-white">
            Enterprise scale. <span className="text-gradient-aurora">Startup speed.</span>
          </h2>
        </motion.div>

        {/* Stats grid */}
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: shouldReduce ? 0 : 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.2 }}
          transition={{ duration: 0.7 }}
          className="rounded-2xl overflow-hidden mb-12"
          style={{
            background: "rgba(255,255,255,0.03)",
            border: "1px solid rgba(255,255,255,0.07)",
            boxShadow: "0 0 0 1px rgba(255,255,255,0.04), 0 8px 40px rgba(0,0,0,0.3)",
          }}
        >
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 divide-x divide-y divide-white/[0.06]">
            {STATS.map((stat, i) => (
              <StatCounter key={stat.label} stat={stat} delay={i * 100} started={started} />
            ))}
          </div>
        </motion.div>

        {/* Certifications marquee */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="relative overflow-hidden"
          aria-label="Certifications and compliance standards"
        >
          <div
            className="absolute left-0 top-0 bottom-0 w-16 z-10 pointer-events-none"
            style={{ background: "linear-gradient(to right, #0a0a0f, transparent)" }}
            aria-hidden="true"
          />
          <div
            className="absolute right-0 top-0 bottom-0 w-16 z-10 pointer-events-none"
            style={{ background: "linear-gradient(to left, #0a0a0f, transparent)" }}
            aria-hidden="true"
          />
          <div className="marquee-track" aria-hidden="true">
            {doubled.map((cert, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full flex-shrink-0 text-xs font-medium"
                style={{
                  background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.07)",
                  color: "rgba(255,255,255,0.45)",
                }}
              >
                <span
                  className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                  style={{ background: "#ed6c00" }}
                />
                {cert}
              </span>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
