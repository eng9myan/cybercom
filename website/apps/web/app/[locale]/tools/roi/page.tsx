import { setRequestLocale } from "next-intl/server";
import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight, TrendingUp, Clock, Users, DollarSign, CheckCircle, BarChart2 } from "lucide-react";

interface ROIPageProps {
  params: Promise<{ locale: string }>;
}

export async function generateMetadata({ params }: ROIPageProps): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  return buildMetadata({
    title: "ROI Calculator",
    description:
      "Calculate the return on investment of deploying CyberCom across your organization. See projected savings on operational costs, staff efficiency, and compliance overhead.",
    path: "/tools/roi",
    locale,
  });
}

const ROI_SCENARIOS = [
  {
    segment: "Mid-size Clinic (50 staff)",
    investment: "$18,000/year",
    savings: [
      { label: "Paper/admin cost reduction", amount: "$24,000" },
      { label: "Staff time saved (billing, reports)", amount: "$18,000" },
      { label: "Error reduction (lab, pharmacy)", amount: "$9,000" },
      { label: "Compliance penalty avoidance", amount: "$6,000" },
    ],
    totalSavings: "$57,000",
    roi: "217%",
    payback: "4 months",
    highlight: false,
  },
  {
    segment: "Regional Hospital (500 staff)",
    investment: "$120,000/year",
    savings: [
      { label: "Paper/EHR migration savings", amount: "$95,000" },
      { label: "Revenue cycle improvement (5%)", amount: "$180,000" },
      { label: "Pharmacy dispensing errors (−70%)", amount: "$60,000" },
      { label: "Staff efficiency (20% time saved)", amount: "$85,000" },
    ],
    totalSavings: "$420,000",
    roi: "250%",
    payback: "3.5 months",
    highlight: true,
  },
  {
    segment: "Government Ministry (Enterprise)",
    investment: "$480,000/year",
    savings: [
      { label: "Legacy system consolidation", amount: "$350,000" },
      { label: "Citizen service digitization", amount: "$280,000" },
      { label: "Procurement savings (CyCom ERP)", amount: "$180,000" },
      { label: "Compliance & audit overhead (−60%)", amount: "$120,000" },
    ],
    totalSavings: "$930,000",
    roi: "94%",
    payback: "6 months",
    highlight: false,
  },
];

const KEY_DRIVERS = [
  {
    icon: Clock,
    title: "Time savings",
    items: [
      "60–80% reduction in manual documentation time",
      "Automated lab result routing — zero manual entry",
      "One-click insurance claim submission",
      "Instant medication dispensing verification",
    ],
  },
  {
    icon: DollarSign,
    title: "Revenue improvement",
    items: [
      "3–8% improvement in billing capture rate",
      "Faster insurance claim approval (avg. 14 → 4 days)",
      "Reduced claim rejection rate (−65%)",
      "Pharmacy revenue tracking with waste reduction",
    ],
  },
  {
    icon: Users,
    title: "Staff efficiency",
    items: [
      "15–25% increase in patient throughput per physician",
      "Nursing documentation time reduced by 40%",
      "Pharmacist verification time cut by 70%",
      "HR/payroll manual processing eliminated",
    ],
  },
  {
    icon: BarChart2,
    title: "Risk & compliance",
    items: [
      "Automated FHIR/ICD-11 compliance checks",
      "Real-time MOH data submission — no penalty risk",
      "Medication error alerts (drug-drug, drug-allergy)",
      "Full audit trail for all clinical actions",
    ],
  },
];

export default async function ROIPage({ params }: ROIPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const l = locale as Locale;

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <div className="relative py-28 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="glow-orb w-[600px] h-[600px] -top-24 right-0 bg-cy-orange/5" />
        </div>
        <div className="section-container relative z-10 text-center">
          <span className="product-badge text-cy-orange border-cy-orange/20 bg-cy-orange/5 mb-6">
            ROI Calculator
          </span>
          <h1 className="text-5xl lg:text-6xl font-heading font-semibold text-white mb-6 leading-tight max-w-3xl mx-auto">
            Measure the value of{" "}
            <span className="text-gradient">CyberCom</span>
          </h1>
          <p className="text-xl text-cy-gray-400 max-w-2xl mx-auto mb-10">
            Based on real customer deployments. See the projected savings and efficiency
            gains for your organization size and product selection.
          </p>
          <Link href={`/${l}/demo`} className="btn-primary px-8 py-3">
            Get a Custom ROI Report
            <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
          </Link>
        </div>
      </div>

      {/* Scenarios */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="scenarios-heading">
        <div className="section-container">
          <h2 id="scenarios-heading" className="text-3xl font-heading font-semibold text-white mb-4 text-center">
            ROI by organization type
          </h2>
          <p className="text-cy-gray-400 text-center mb-12 max-w-xl mx-auto">
            Figures based on median outcomes across CyberCom customer deployments in the MENA region.
          </p>
          <div className="grid lg:grid-cols-3 gap-5">
            {ROI_SCENARIOS.map((sc) => (
              <div
                key={sc.segment}
                className={`glass-card p-8 rounded-2xl flex flex-col ${sc.highlight ? "border-cy-orange/40" : "border-cy-glass-border"}`}
              >
                {sc.highlight && (
                  <span className="text-2xs font-semibold text-cy-orange mb-3">Most Common</span>
                )}
                <h3 className="text-lg font-heading font-semibold text-white mb-1">{sc.segment}</h3>
                <p className="text-sm text-cy-gray-400 mb-6">Investment: {sc.investment}</p>

                <div className="space-y-3 mb-6 flex-1">
                  {sc.savings.map((s) => (
                    <div key={s.label} className="flex items-center justify-between gap-2">
                      <span className="text-xs text-cy-gray-400 flex-1">{s.label}</span>
                      <span className="text-xs font-semibold text-white whitespace-nowrap">{s.amount}</span>
                    </div>
                  ))}
                </div>

                <div className="h-px bg-cy-glass-border mb-5" />

                <div className="grid grid-cols-3 gap-3 text-center">
                  <div>
                    <div className="text-xl font-heading font-bold text-cy-orange">{sc.roi}</div>
                    <div className="text-2xs text-cy-gray-400">3-Year ROI</div>
                  </div>
                  <div>
                    <div className="text-xl font-heading font-bold text-white">{sc.totalSavings}</div>
                    <div className="text-2xs text-cy-gray-400">Total Savings</div>
                  </div>
                  <div>
                    <div className="text-xl font-heading font-bold text-white">{sc.payback}</div>
                    <div className="text-2xs text-cy-gray-400">Payback</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <p className="text-xs text-cy-gray-500 text-center mt-6">
            * Figures are indicative and based on median customer outcomes. Individual results may vary by organization size, existing systems, and deployment scope.
          </p>
        </div>
      </section>

      {/* Key drivers */}
      <section className="py-20" aria-labelledby="drivers-heading">
        <div className="section-container">
          <h2 id="drivers-heading" className="text-3xl font-heading font-semibold text-white mb-4 text-center">
            What drives the returns
          </h2>
          <p className="text-cy-gray-400 text-center mb-12 max-w-xl mx-auto">
            CyberCom generates measurable ROI across four core drivers in every deployment.
          </p>
          <div className="grid md:grid-cols-2 gap-6">
            {KEY_DRIVERS.map((driver) => {
              const Icon = driver.icon;
              return (
                <div key={driver.title} className="glass-card p-8 rounded-2xl">
                  <div className="flex items-center gap-3 mb-5">
                    <div className="w-10 h-10 rounded-xl bg-cy-glass-bg border border-cy-glass-border flex items-center justify-center">
                      <Icon className="w-5 h-5 text-cy-orange" aria-hidden="true" />
                    </div>
                    <h3 className="text-lg font-heading font-semibold text-white capitalize">{driver.title}</h3>
                  </div>
                  <ul className="space-y-2.5">
                    {driver.items.map((item) => (
                      <li key={item} className="flex items-start gap-2 text-sm text-cy-gray-300">
                        <CheckCircle className="w-4 h-4 text-cy-orange flex-shrink-0 mt-0.5" aria-hidden="true" />
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

      {/* ROI trend visual */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="trend-heading">
        <div className="section-container max-w-3xl">
          <h2 id="trend-heading" className="text-3xl font-heading font-semibold text-white mb-4 text-center">
            Cumulative returns over 3 years
          </h2>
          <p className="text-cy-gray-400 text-center mb-10">Regional hospital benchmark (500 staff)</p>
          <div className="glass-card p-8 rounded-2xl space-y-4" aria-label="3-year ROI chart for 500-staff hospital">
            {[
              { year: "Year 1", investment: 120, returns: 280, net: "+$160K" },
              { year: "Year 2", investment: 120, returns: 420, net: "+$300K" },
              { year: "Year 3", investment: 120, returns: 420, net: "+$300K" },
            ].map((row) => (
              <div key={row.year}>
                <div className="flex items-center justify-between text-xs text-cy-gray-400 mb-1.5">
                  <span>{row.year}</span>
                  <span className="text-cy-orange font-semibold">{row.net}</span>
                </div>
                <div className="relative h-6 rounded-lg overflow-hidden bg-cy-glass-bg">
                  <div
                    className="absolute inset-y-0 left-0 bg-cy-orange/20 rounded-lg"
                    style={{ width: `${(row.investment / 420) * 100}%` }}
                    aria-label={`Investment $${row.investment}K`}
                  />
                  <div
                    className="absolute inset-y-0 left-0 bg-cy-orange rounded-lg"
                    style={{ width: `${(row.returns / 420) * 100}%`, opacity: 0.7 }}
                    aria-label={`Returns $${row.returns}K`}
                  />
                </div>
                <div className="flex gap-4 mt-1 text-2xs text-cy-gray-500">
                  <span>Investment: ${row.investment}K</span>
                  <span>Returns: ${row.returns}K</span>
                </div>
              </div>
            ))}
            <div className="flex items-center gap-4 pt-2">
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-sm bg-cy-orange/20" aria-hidden="true" />
                <span className="text-2xs text-cy-gray-400">Investment</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-sm bg-cy-orange/70" aria-hidden="true" />
                <span className="text-2xs text-cy-gray-400">Cumulative Returns</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20" aria-labelledby="roi-cta">
        <div className="section-container max-w-2xl text-center">
          <TrendingUp className="w-10 h-10 text-cy-orange mx-auto mb-6" aria-hidden="true" />
          <h2 id="roi-cta" className="text-3xl font-heading font-semibold text-white mb-4">
            Get your custom ROI report
          </h2>
          <p className="text-cy-gray-400 mb-8">
            Our team will build a detailed ROI analysis tailored to your organization, existing systems,
            and product selection — free, with no commitment required.
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <Link href={`/${l}/demo`} className="btn-primary px-8 py-3">
              Request ROI Analysis
              <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
            </Link>
            <Link href={`/${l}/tools/compare`} className="btn-secondary px-8 py-3">
              Compare Products
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
