import { setRequestLocale } from "next-intl/server";
import type { Metadata } from "next";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { Shield, Lock, Eye, CheckCircle2, Server, Globe, FileText } from "lucide-react";
import Link from "next/link";

interface SecurityPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: SecurityPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  return buildMetadata({
    title: "Security & Trust Center",
    description: "CyberCom's security posture, compliance certifications, data residency policies, and responsible disclosure program.",
    path: "/security",
    locale,
  });
}

const CERTS = [
  {
    name: "FHIR R4",
    category: "Healthcare Interoperability",
    desc: "HL7 FHIR Release 4 native implementation across all CyMed modules. SMART on FHIR for third-party app authorization.",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
  },
  {
    name: "ISO 27001",
    category: "Information Security",
    desc: "Information security management system aligned to ISO/IEC 27001 controls. Annual third-party audit.",
    color: "text-blue-400",
    bg: "bg-blue-500/10",
    border: "border-blue-500/20",
  },
  {
    name: "SOC 2 Type II",
    category: "Cloud Security",
    desc: "Security, availability, and confidentiality controls independently audited by a licensed CPA firm.",
    color: "text-violet-400",
    bg: "bg-violet-500/10",
    border: "border-violet-500/20",
  },
  {
    name: "HIPAA Ready",
    category: "Healthcare Privacy",
    desc: "Administrative, physical, and technical safeguards supporting HIPAA compliance. BAA available for US-linked deployments.",
    color: "text-cyan-400",
    bg: "bg-cyan-500/10",
    border: "border-cyan-500/20",
  },
  {
    name: "GDPR Ready",
    category: "Data Privacy",
    desc: "Data processing agreements, right-to-erasure workflows, consent management, and DPA templates for EU-linked customers.",
    color: "text-teal-400",
    bg: "bg-teal-500/10",
    border: "border-teal-500/20",
  },
  {
    name: "PCI-DSS",
    category: "Payment Security",
    desc: "PCI-DSS level controls for CyShop payment processing. Tokenization at point of capture — no raw card data stored.",
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    border: "border-amber-500/20",
  },
  {
    name: "ZATCA e-Invoice",
    category: "GCC Tax Compliance",
    desc: "KSA ZATCA Phase 1 and Phase 2 compliant. Cryptographic signing, clearance mode, and reporting mode for all VAT invoices.",
    color: "text-orange-400",
    bg: "bg-orange-500/10",
    border: "border-orange-500/20",
  },
  {
    name: "OAuth 2.1 / OIDC",
    category: "Identity & Access",
    desc: "CyIdentity implements OAuth 2.1, OIDC, PKCE, passkeys (WebAuthn), and device-bound tokens. Zero Trust by default.",
    color: "text-indigo-400",
    bg: "bg-indigo-500/10",
    border: "border-indigo-500/20",
  },
];

const PILLARS = [
  {
    icon: Lock,
    title: "Encryption",
    items: [
      "TLS 1.3 in transit — no fallback to older versions",
      "AES-256 at rest for all data stores",
      "Field-level encryption for PHI and PII",
      "Hardware-backed key management (HSM/KMS)",
    ],
  },
  {
    icon: Eye,
    title: "Access Control",
    items: [
      "Role-Based Access Control (RBAC) + Attribute-Based (ABAC)",
      "Mandatory MFA for all clinical and admin roles",
      "Break-Glass emergency access with automatic audit alert",
      "Privileged access management (PAM) for infrastructure",
    ],
  },
  {
    icon: Server,
    title: "Infrastructure",
    items: [
      "Isolated tenant environments — no shared compute",
      "99.9% uptime SLA with active-active failover",
      "Daily encrypted backups with 90-day retention",
      "Vulnerability scanning and SAST/DAST in CI/CD pipeline",
    ],
  },
  {
    icon: Globe,
    title: "Data Residency",
    items: [
      "Jordan: on-premise or Aqaba SEZ Cloud Zone",
      "KSA: AWS Riyadh / dedicated data center",
      "UAE: Dubai / Abu Dhabi cloud region",
      "Cross-border transfer only with customer written consent",
    ],
  },
  {
    icon: FileText,
    title: "Audit & Logging",
    items: [
      "Immutable hash-chained audit trail (who-what-when-where)",
      "SIEM integration via syslog / webhook",
      "90-day hot log retention, 7-year cold archive for healthcare",
      "Patient access log report available on demand",
    ],
  },
  {
    icon: Shield,
    title: "Incident Response",
    items: [
      "24/7 Security Operations Center (SOC)",
      "Mean time to detect (MTTD) < 15 minutes",
      "Breach notification within 72 hours per GDPR / local law",
      "Dedicated customer security liaison during incidents",
    ],
  },
];

export default async function SecurityPage({ params }: SecurityPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;

  return (
    <main className="pt-24 pb-20">

      {/* Hero */}
      <section className="py-16 relative overflow-hidden">
        <div
          className="absolute inset-0 pointer-events-none"
          aria-hidden="true"
          style={{ background: "radial-gradient(ellipse at 50% 0%, rgba(89,195,225,0.06) 0%, transparent 70%)" }}
        />
        <div className="section-container text-center relative z-10">
          <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full border border-white/[0.09] bg-white/[0.04] mb-8">
            <Shield className="w-4 h-4 text-cy-cyan" />
            <span className="text-xs font-medium text-white/55 tracking-widest uppercase">
              Security &amp; Trust Center
            </span>
          </div>
          <h1 className="text-4xl lg:text-6xl font-heading font-semibold text-white mb-6 max-w-4xl mx-auto">
            Security by design.<br />
            <span className="text-gradient-aurora">Compliance by default.</span>
          </h1>
          <p className="text-lg text-white/45 max-w-2xl mx-auto leading-relaxed mb-10">
            Healthcare and enterprise data demands the highest protection. CyberCom builds security
            into every layer — from protocol to process to people.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href={`/${l}/demo`} className="btn-primary-glow px-8 py-3.5">
              Request Security Review
            </Link>
            <a href="mailto:security@cy-com.com" className="btn-secondary px-8 py-3.5">
              security@cy-com.com
            </a>
          </div>
        </div>
      </section>

      {/* Certifications */}
      <section className="py-16" aria-labelledby="cert-heading">
        <div className="section-container">
          <div className="text-center mb-12">
            <p className="text-xs font-semibold uppercase tracking-widest text-cy-orange mb-3">Certifications &amp; Standards</p>
            <h2 id="cert-heading" className="text-3xl font-heading font-semibold text-white">
              Every certification we carry matters for your industry
            </h2>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {CERTS.map((cert) => (
              <div key={cert.name} className="glass-card p-5 rounded-2xl">
                <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold mb-4 border ${cert.bg} ${cert.border} ${cert.color}`}>
                  <CheckCircle2 className="w-3 h-3" />
                  {cert.name}
                </div>
                <p className="text-xs text-cy-gray-400 mb-1">{cert.category}</p>
                <p className="text-sm text-white/70 leading-relaxed">{cert.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Security pillars */}
      <section className="py-16 bg-cy-dark/30" aria-labelledby="pillars-heading">
        <div className="section-container">
          <div className="text-center mb-12">
            <p className="text-xs font-semibold uppercase tracking-widest text-cy-orange mb-3">Security Architecture</p>
            <h2 id="pillars-heading" className="text-3xl font-heading font-semibold text-white">
              Six-layer security posture
            </h2>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {PILLARS.map((pillar) => {
              const Icon = pillar.icon;
              return (
                <div key={pillar.title} className="glass-card p-6 rounded-2xl">
                  <div className="w-10 h-10 rounded-xl bg-cy-orange/10 border border-cy-orange/20 flex items-center justify-center mb-4">
                    <Icon className="w-5 h-5 text-cy-orange" />
                  </div>
                  <h3 className="font-heading font-semibold text-white mb-4">{pillar.title}</h3>
                  <ul className="space-y-2">
                    {pillar.items.map((item) => (
                      <li key={item} className="flex items-start gap-2 text-sm text-cy-gray-400">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Responsible disclosure */}
      <section className="py-16" aria-labelledby="disclosure-heading">
        <div className="section-container max-w-3xl mx-auto text-center">
          <h2 id="disclosure-heading" className="text-2xl font-heading font-semibold text-white mb-4">
            Responsible Disclosure
          </h2>
          <p className="text-white/50 mb-6 leading-relaxed">
            We operate a responsible disclosure program. If you discover a security vulnerability
            in any CyberCom product, please contact us directly. We acknowledge reports within
            24 hours and commit to keeping researchers updated throughout the remediation process.
          </p>
          <a
            href="mailto:security@cy-com.com"
            className="btn-primary inline-flex items-center gap-2"
          >
            <Shield className="w-4 h-4" />
            Report a Vulnerability
          </a>
          <p className="text-xs text-white/30 mt-4">
            PGP key available on request · We do not pursue legal action against good-faith reporters
          </p>
        </div>
      </section>

    </main>
  );
}
