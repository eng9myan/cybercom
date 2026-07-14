"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { useParams } from "next/navigation";
import {
  ArrowRight, Building2, Stethoscope, FlaskConical, Pill, ScanLine, ShieldCheck,
  FileCheck2, Brain, Lock, Globe2, Check, Play, ExternalLink, Activity
} from "lucide-react";

const CYMED_URL = process.env.NEXT_PUBLIC_CYMED_URL ?? "https://cymed.cy-com.com";

const VERTICALS = [
  { icon: Stethoscope, slug: "cymed-clinic", name: "Clinic", desc: "Outpatient reception, appointments, consultations, triage, telemedicine, and referrals for clinics and specialty practices.", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  { icon: Building2, slug: "cymed-hospital", name: "Hospital", desc: "ADT, bed management, emergency, inpatient, nursing, ICU, OR, anesthesia, maternity, and discharge — full inpatient operations.", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  { icon: FlaskConical, slug: "cymed-laboratory", name: "Laboratory", desc: "Specimen accessioning, worklists, microbiology, pathology, histopathology, QC, and reference lab integration.", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  { icon: ScanLine, slug: "cymed-imaging", name: "Imaging", desc: "Modality worklist, radiology reporting, PACS gateway, DICOM registry, and teleradiology.", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  { icon: Pill, slug: "cymed-pharmacy", name: "Pharmacy", desc: "Prescriptions, dispensing, clinical pharmacy review, drug interaction checks, formulary, and medication reconciliation.", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
];

const FEATURES = [
  { icon: FileCheck2, title: "FHIR R4/R5 Native", desc: "Every module speaks FHIR. Patients, encounters, orders, and results share one clinical data model across the care continuum.", color: "text-emerald-400" },
  { icon: ShieldCheck, title: "ICD-11 & SNOMED CT", desc: "Diagnoses and clinical findings coded to international standards from day one — no bolt-on terminology mapping.", color: "text-teal-400" },
  { icon: Lock, title: "Consent & Break Glass", desc: "Patient consent tracked per data category. Emergency access is logged, time-boxed, and requires a documented reason.", color: "text-sky-400" },
  { icon: Activity, title: "Hash-Chained Audit", desc: "Every clinical read and write is recorded in a tamper-evident audit trail — required for every sensitive operation.", color: "text-amber-400" },
  { icon: Brain, title: "CyAI — Advisory Only", desc: "Clinical decision support surfaces relevant history, interactions, and coding suggestions. It never autonomously diagnoses or prescribes — a clinician always decides.", color: "text-pink-400" },
  { icon: Globe2, title: "Arabic & English", desc: "Full RTL and LTR clinical interfaces, so staff work in the language they're trained in.", color: "text-violet-400" },
];

const WORKFLOW_STEPS = [
  { step: 1, title: "Choose Your Modules", desc: "Select the CyMed editions your facility needs — Clinic, Hospital, Laboratory, Imaging, Pharmacy — and configure for your specialty." },
  { step: 2, title: "Provision Tenant & Staff", desc: "CyIdentity provisions your organization with role-based access for providers, nurses, technicians, and administrators." },
  { step: 3, title: "Migrate Patient Records", desc: "Import existing records via FHIR or CSV. Connect lab analyzers and PACS through CyIntegrationHub." },
  { step: 4, title: "Clinical Validation", desc: "Complete UAT for every clinical workflow before go-live. No module ships without a validation pass." },
  { step: 5, title: "Go Live & Expand", desc: "Launch with hypercare support. Add modules as your facility grows — one shared patient record throughout." },
];

const EDITIONS = [
  { name: "Clinic", price: "For outpatient practices", features: ["Appointments & scheduling", "Consultations & SOAP notes", "e-Prescriptions", "Triage & queues", "Referrals", "Email support"] },
  { name: "Hospital", price: "For hospitals & multi-department facilities", popular: true, features: ["Everything in Clinic", "ADT & bed management", "ICU / OR / Emergency", "Nursing & discharge", "Capacity management", "Priority support"] },
  { name: "Enterprise", price: "For hospital groups & networks", features: ["All modules included", "Multi-facility organizations", "Custom integrations", "API access", "Dedicated account manager", "24/7 SLA"] },
];

export default function CyMedPage() {
  const params = useParams();
  const locale = (params?.locale as string) ?? "en";
  const l = locale;
  const shouldReduce = useReducedMotion();

  const fadeUp = {
    hidden: { opacity: 0, y: shouldReduce ? 0 : 24 },
    visible: (delay: number) => ({
      opacity: 1, y: 0,
      transition: { duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] },
    }),
  };

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <section className="relative min-h-[85vh] flex items-center overflow-hidden" aria-labelledby="cymed-heading">
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          <div className="glow-orb w-[800px] h-[800px] -top-32 left-1/2 -translate-x-1/2 bg-emerald-500/8 animate-glow-pulse" />
          <div className="glow-orb w-[500px] h-[500px] bottom-0 -right-32 bg-teal-500/6" />
          <div className="absolute inset-0 opacity-[0.025]" style={{ backgroundImage: `linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)`, backgroundSize: "64px 64px" }} />
        </div>
        <div className="section-container relative z-10">
          <div className="max-w-4xl">
            <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={0} className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/5 mb-8">
              <Stethoscope className="w-3.5 h-3.5 text-emerald-400" aria-hidden="true" />
              <span className="text-xs font-medium text-emerald-400 tracking-wider uppercase">CyMed · Intelligent Healthcare Platform</span>
            </motion.div>
            <motion.h1 id="cymed-heading" variants={fadeUp} initial="hidden" animate="visible" custom={0.1} className="text-5xl sm:text-6xl lg:text-7xl font-heading font-semibold text-white mb-6 leading-tight">
              One Patient Record{" "}<br />
              <span className="text-gradient-orange">Across Every Care Setting</span>
            </motion.h1>
            <motion.p variants={fadeUp} initial="hidden" animate="visible" custom={0.2} className="text-xl text-cy-gray-400 leading-relaxed mb-4 max-w-2xl">
              FHIR-native, ICD-11 coded clinical platform for hospitals, clinics, laboratories, imaging centers, and pharmacies — one data model, one identity, one audit trail.
            </motion.p>
            <motion.p variants={fadeUp} initial="hidden" animate="visible" custom={0.25} className="text-base text-cy-gray-400 mb-8 max-w-2xl">
              Part of the CyberCom ecosystem. Shares CyIdentity, CyAudit, and CyIntegrationHub with CyShop and CyCom ERP.
            </motion.p>
            <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={0.3} className="flex flex-wrap gap-3">
              <a href={CYMED_URL} target="_blank" rel="noreferrer" className="btn-primary px-7 py-3.5 text-sm inline-flex items-center gap-2">
                <Play className="w-4 h-4" aria-hidden="true" />
                Launch Demo
                <ExternalLink className="w-3.5 h-3.5 opacity-70" aria-hidden="true" />
              </a>
              <Link href={`/${l}/demo?product=cymed`} className="btn-secondary px-7 py-3.5 text-sm inline-flex items-center gap-2">
                Request a Demo
                <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
              </Link>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Verticals */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="verticals-heading">
        <div className="section-container">
          <div className="text-center mb-14">
            <h2 id="verticals-heading" className="text-3xl font-heading font-semibold text-white mb-4">Every Care Setting, One Platform</h2>
            <p className="text-cy-gray-400 max-w-2xl mx-auto">CyMed covers the full clinical continuum. Deploy one module or the full suite — they share a single patient record from day one.</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {VERTICALS.map((v, i) => (
              <motion.div
                key={v.slug}
                variants={fadeUp}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                custom={i * 0.05}
              >
                <Link
                  href={`/${l}/products/${v.slug}`}
                  className={`glass-card block rounded-xl p-5 border h-full ${v.bg} hover:scale-[1.01] transition-all duration-200`}
                >
                  <div className={`w-9 h-9 rounded-lg flex items-center justify-center border mb-3 ${v.bg}`}>
                    <v.icon className={`w-4.5 h-4.5 ${v.color}`} aria-hidden="true" />
                  </div>
                  <h3 className={`text-sm font-heading font-semibold ${v.color} mb-1.5`}>{v.name}</h3>
                  <p className="text-xs text-cy-gray-400 leading-relaxed">{v.desc}</p>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20" aria-labelledby="features-heading">
        <div className="section-container">
          <div className="text-center mb-14">
            <h2 id="features-heading" className="text-3xl font-heading font-semibold text-white mb-4">Built for Clinical Safety</h2>
            <p className="text-cy-gray-400 max-w-2xl mx-auto">Standards-based interoperability and auditability, not an afterthought bolted onto a generic EMR.</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((f, i) => (
              <motion.div
                key={f.title}
                variants={fadeUp}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                custom={i * 0.05}
                className="glass-card rounded-xl p-6 flex gap-4"
              >
                <div className={`w-10 h-10 rounded-xl bg-cy-dark border border-cy-glass-border flex items-center justify-center flex-shrink-0`}>
                  <f.icon className={`w-5 h-5 ${f.color}`} aria-hidden="true" />
                </div>
                <div>
                  <h3 className="text-sm font-heading font-semibold text-white mb-1.5">{f.title}</h3>
                  <p className="text-xs text-cy-gray-400 leading-relaxed">{f.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Workflow */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="workflow-heading">
        <div className="section-container max-w-4xl mx-auto">
          <div className="text-center mb-14">
            <h2 id="workflow-heading" className="text-3xl font-heading font-semibold text-white mb-4">How CyMed Rolls Out</h2>
            <p className="text-cy-gray-400">From tenant provisioning to clinical go-live, with validation at every step.</p>
          </div>
          <div className="space-y-4">
            {WORKFLOW_STEPS.map((step) => (
              <div key={step.step} className="glass-card rounded-xl p-6 flex gap-5 items-start">
                <div className="w-8 h-8 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center flex-shrink-0 text-sm font-bold text-emerald-400">{step.step}</div>
                <div>
                  <h3 className="text-sm font-heading font-semibold text-white mb-1.5">{step.title}</h3>
                  <p className="text-sm text-cy-gray-400 leading-relaxed">{step.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Editions */}
      <section className="py-20" aria-labelledby="editions-heading">
        <div className="section-container">
          <div className="text-center mb-14">
            <h2 id="editions-heading" className="text-3xl font-heading font-semibold text-white mb-4">Choose Your Edition</h2>
            <p className="text-cy-gray-400 max-w-xl mx-auto">Start with the modules your facility needs today. All editions include cloud hosting, updates, and core support.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {EDITIONS.map((ed) => (
              <div key={ed.name} className={`glass-card rounded-2xl p-7 flex flex-col ${ed.popular ? "border-emerald-500/40 ring-1 ring-emerald-500/20" : ""}`}>
                {ed.popular && (
                  <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-xs font-medium text-emerald-400 mb-4 self-start">
                    <Check className="w-3 h-3 fill-emerald-400" aria-hidden="true" />
                    Most Common
                  </div>
                )}
                <h3 className="text-xl font-heading font-semibold text-white mb-1">{ed.name}</h3>
                <p className="text-xs text-cy-gray-400 mb-5">{ed.price}</p>
                <ul className="space-y-2.5 mb-7 flex-1" aria-label={`${ed.name} plan features`}>
                  {ed.features.map((f) => (
                    <li key={f} className="flex items-start gap-2.5">
                      <Check className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" aria-hidden="true" />
                      <span className="text-sm text-cy-gray-200">{f}</span>
                    </li>
                  ))}
                </ul>
                <Link href={`/${l}/demo?product=cymed`} className={`w-full text-center py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${ed.popular ? "btn-primary" : "btn-secondary"}`}>
                  Get Started
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20" aria-labelledby="cta-heading">
        <div className="section-container text-center max-w-3xl mx-auto">
          <h2 id="cta-heading" className="text-3xl font-heading font-semibold text-white mb-4">Ready to Modernize Clinical Care?</h2>
          <p className="text-cy-gray-400 mb-8">See CyMed's clinic, hospital, laboratory, imaging, and pharmacy modules working from one patient record.</p>
          <div className="flex flex-wrap gap-3 justify-center">
            <a href={CYMED_URL} target="_blank" rel="noreferrer" className="btn-primary px-8 py-3 text-sm inline-flex items-center gap-2">
              <Play className="w-4 h-4" aria-hidden="true" />
              Launch CyMed Demo
              <ExternalLink className="w-3.5 h-3.5 opacity-70" aria-hidden="true" />
            </a>
            <Link href={`/${l}/contact`} className="btn-secondary px-8 py-3 text-sm">
              Contact Sales
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
