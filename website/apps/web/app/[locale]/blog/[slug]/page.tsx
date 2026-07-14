import { setRequestLocale } from "next-intl/server";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowLeft, Calendar, Clock, Tag, User } from "lucide-react";

interface ArticlePageProps {
  params: Promise<{ locale: string; slug: string }>;
}

const ARTICLES_CONTENT: Record<
  string,
  {
    title: string;
    category: string;
    date: string;
    readTime: string;
    author: string;
    authorRole: string;
    paragraphs: string[];
  }
> = {
  "fhir-r4-interoperability-mena": {
    title: "FHIR R4 and the Future of Healthcare Interoperability in MENA",
    category: "Healthcare IT",
    date: "2026-06-15",
    readTime: "8 min read",
    author: "Dr. Tariq Al-Mansoor",
    authorRole: "Chief Medical Information Officer",
    paragraphs: [
      "Interoperability has historically been the greatest challenge in healthcare technology. Across the Middle East and North Africa (MENA) region, the fragmentation of Electronic Health Records (EMR) has isolated patient data within single hospitals or clinic groups. However, the regulatory landscape is shifting rapidly. National health mandates across the GCC are now requiring healthcare organizations to support standardized data exchange.",
      "At the center of this transformation is the HL7 Fast Healthcare Interoperability Resources (FHIR) R4 standard. Unlike legacy HL7 v2 messaging, which relies on rigid, non-standardized pipe-delimited text blocks, FHIR utilizes modern JSON-based API payloads. It exposes clinical concepts—such as Patients, Encounters, Observations, and MedicationRequests—as discrete, addressable REST resources.",
      "CyberCom's clinical suite, CyMed, was engineered from day one with a FHIR-native datastore. Rather than treating FHIR as a translation layer on top of a relational database, CyMed stores and processes clinical data natively in FHIR resource models. This architecture eliminates the need for expensive data transformations, minimizes latency during cross-facility transfers, and guarantees that all record exchanges adhere strictly to international schemas.",
      "As ministries of health across Saudi Arabia, the United Arab Emirates, and Jordan roll out national health insurance systems and unified health records (e.g., NPHIES and Malaffi), FHIR-native architectures like CyMed are becoming a strategic necessity. By eliminating data silos, hospitals can seamlessly share lab results, imaging reports, and medication histories, improving clinical safety and reducing duplicate testing."
    ],
  },
  "icd-11-clinical-coding-readiness": {
    title: "ICD-11 Readiness: What Healthcare Organizations Need to Know",
    category: "Clinical",
    date: "2026-06-08",
    readTime: "6 min read",
    author: "Dr. Sarah Miller",
    authorRole: "Director of Clinical Quality",
    paragraphs: [
      "The transition from ICD-10 to the International Classification of Diseases 11th Revision (ICD-11) is one of the most significant upgrades in clinical terminology in three decades. Adopted by the World Health Organization (WHO), ICD-11 provides a completely digital, multilingual classification system designed to capture today's complex clinical concepts.",
      "A key innovation of ICD-11 is 'post-coordination.' In ICD-10, coders had to browse a static list of pre-coordinated codes, which often lacked specific details. ICD-11 allows clinicians to combine a stem code with multiple extension codes to represent precise clinical concepts—such as the exact anatomical site of a fracture, the severity of a burn, or whether a condition was present on admission.",
      "CyMed incorporates this post-coordination logic directly inside the physician's documentation flow. As a provider writes a SOAP note, the clinical terminology registry suggests matching ICD-11 stem codes and dynamically generates the post-coordinated extensions. By linking these codes to SNOMED CT terminology, CyMed creates a structured clinical record that satisfies both international medical registries and local insurance billing requirements.",
      "Preparation is key. Healthcare executives should begin training clinical and billing teams now. Transitioning early ensures that your organization avoids disruption in claims submissions, captures patient complexity accurately, and is ready for the upcoming regulatory mandates."
    ],
  },
  "drug-interaction-engine-design": {
    title: "How CyberCom Built a 5-Type Drug Interaction Engine",
    category: "Clinical",
    date: "2026-06-01",
    readTime: "10 min read",
    author: "Firas Al-Najjar, PharmD",
    authorRole: "Lead Clinical Pharmacist",
    paragraphs: [
      "Medication errors remain a leading cause of preventable harm in healthcare settings worldwide. In busy hospitals and pharmacies, clinical decision support must act as an active, intelligent guardrail. Standard EMR databases often restrict checks to simple drug-drug conflicts, leading to 'alert fatigue' where clinicians override warnings because they lack clinical context.",
      "To address this, the CyMed Pharmacy module features an advanced 5-type drug interaction engine. When a provider enters a FHIR MedicationRequest, the system instantly evaluates the order across five distinct safety dimensions:",
      "1. Drug-Drug Interactions: Checks for pharmacological conflicts between the newly prescribed drug and the patient's active medications. 2. Drug-Allergy Interactions: Cross-references the drug's active ingredients and classes against the patient's recorded drug allergies. 3. Drug-Disease Interactions: Analyzes patient diagnoses (ICD-11) to flag contraindications (e.g., prescribing NSAIDs for a patient with severe renal failure). 4. Drug-Age/Pediatric Checks: Warns if the dosage is inappropriate for geriatric or pediatric patients. 5. Duplicate Therapy: Flags if the patient is already taking a drug from the same therapeutic class.",
      "All checks are executed in under 20 milliseconds at the database level and presented as advisory-only cards in the provider UI. By structuring alerts by severity (Critical, High, Moderate) and providing clear justifications, the engine reduces alert fatigue and empowers pharmacists and doctors to make safer prescribing decisions."
    ],
  },
  "zero-trust-healthcare-identity": {
    title: "Zero Trust Identity in Healthcare: From Theory to Production",
    category: "Platform",
    date: "2026-05-25",
    readTime: "7 min read",
    author: "Ali Al-Ghamdi",
    authorRole: "Chief Information Security Officer",
    paragraphs: [
      "Healthcare networks are prime targets for cyberattacks. The sensitivity of personal health data combined with the necessity for instant access makes identity management a complex challenge. Traditional perimeter security ('castle and moat') is no longer sufficient. Healthcare must adopt Zero Trust principles: never trust, always verify.",
      "CyIdentity, the identity and access management (IAM) platform for the CyberCom ecosystem, is built on OAuth 2.1, OpenID Connect (OIDC), and Keycloak 24. It secures every API request across the platforms using temporary cryptographically signed JWT tokens, protecting data access based on the user's validated context.",
      "A critical security requirement in clinical systems is 'Break Glass' emergency access. If a patient is admitted in critical condition, providers must access their medical history immediately, even if they lack explicit system permissions. CyIdentity handles this by allowing providers to override standard access control with a single click. When triggered, the system temporarily elevates privileges while automatically sending an alert to the security team and logging the event in an immutable, hash-chained audit trail.",
      "By combining multi-factor authentication (MFA), role-based and attribute-based access control (RBAC/ABAC), and automated auditing, CyIdentity delivers Zero Trust security without compromising clinical workflow velocity during critical situations."
    ],
  },
  "government-digital-transformation-gcc": {
    title: "Digital Government in the GCC: Architecture Patterns That Work",
    category: "Government",
    date: "2026-05-18",
    readTime: "9 min read",
    author: "Mansour Bin Fahd",
    authorRole: "Enterprise SaaS Architect",
    paragraphs: [
      "Government digital transformation programs across the GCC share unique requirements: citizen identity verification, inter-agency data integration, strict local data sovereignty, and complete bilingual (English/Arabic) support. Standard off-the-shelf software rarely fits these specifications.",
      "CyGov was designed from the ground up to address these specific needs. Built on an API-first microservices architecture, CyGov separates public citizen portals from back-office workflows. This allows ministries to deploy citizen-facing portals (via CyCitizen) while keeping core processing secure behind government firewalls.",
      "Inter-agency integration is achieved using secure REST APIs and event-driven architectures. When a citizen requests a business license, CyGov communicates with national registries, commercial databases, and municipal systems to verify eligibility in real time. Fees are collected through integrated national payment gateways, and the finalized document is delivered directly to the citizen's secure digital wallet.",
      "Our deployment models support local cloud hosting, private government clouds, and air-gapped systems. This flexibility ensures compliance with national data residency regulations while enabling public institutions to scale citizen services effectively."
    ],
  },
  "postgresql-rls-multi-tenancy": {
    title: "Row-Level Security Multi-Tenancy in PostgreSQL: A Production Guide",
    category: "Platform",
    date: "2026-05-10",
    readTime: "12 min read",
    author: "Elena Rostova",
    authorRole: "Principal Software Engineer",
    paragraphs: [
      "Multi-tenancy is the foundation of SaaS applications. In enterprise software, particularly in healthcare and finance, tenant isolation must be absolute. PostgreSQL Row-Level Security (RLS) offers an elegant, database-enforced approach to data isolation, allowing multiple tenants to share a single database cluster securely.",
      "The CyberCom Platform implements RLS using tenant session variables. When a request enters the backend, the `TenantIsolationMiddleware` extracts the tenant ID from the authenticated user's JWT claim. Before executing any database query, it sets a local session parameter: `SET LOCAL app.current_tenant_id = 'tenant-uuid'`. PostgreSQL policies then filter all select, insert, update, and delete operations based on this variable.",
      "This database-enforced isolation provides a major security advantage: even if a developer forgets to filter by tenant in their application code, the database will refuse to return rows belonging to other tenants. This design minimizes the risk of accidental data leaks.",
      "To optimize performance with RLS, we implement composite indexes on `(tenant_id, id)` and tune connection poolers to handle the session parameter overhead. The result is a secure, high-performance multi-tenant architecture ready for enterprise scale."
    ],
  },
  "healthcare-erp-integration-patterns": {
    title: "Connecting Clinical and Financial: Healthcare ERP Integration Patterns",
    category: "Enterprise",
    date: "2026-05-02",
    readTime: "7 min read",
    author: "Yousef Al-Harbi",
    authorRole: "Lead Full-Stack Engineer",
    paragraphs: [
      "A common source of operational inefficiency in healthcare organizations is the division between clinical systems (EMR) and financial platforms (ERP). Doctors document care in EMRs, while billing teams manage finances in separate ERP databases. This separation leads to manual data entry errors, delayed claims, and lost revenue.",
      "To bridge this gap, CyMed integrates directly with CyCom ERP. Using event-driven integration patterns, the system automatically links clinical encounters to financial ledgers without duplicating code or data.",
      "When a provider completes a clinical consultation in CyMed, the system fires an event to CyIntegrationHub. This event triggers the billing service to verify the patient's insurance eligibility and generate an invoice. The invoice lines, containing ICD-11 diagnoses and CPT procedures, are automatically mapped to CyCom's General Ledger (GL) accounts.",
      "This integration ensures that financial metrics (RPS, outstanding balance, accounts receivable) are kept in sync with clinical activity in real time. It speeds up the revenue cycle, reduces billing errors, and gives hospital executives immediate visibility into financial performance."
    ],
  },
  "cybercom-release-2-production-readiness": {
    title: "CyberCom Release 2: Production Readiness Assessment",
    category: "Platform",
    date: "2026-04-28",
    readTime: "5 min read",
    author: "Mohammad Alnsour",
    authorRole: "Release Manager",
    paragraphs: [
      "The upcoming Release 2 of the CyberCom Platform represents a major milestone. In this assessment, we review the platform's production readiness, focusing on SaaS multi-tenancy, white-labeling, licensing, and compliance.",
      "Our engineering team has successfully resolved the core integration gaps. The platform backend test suite now contains 1,213 successful tests, confirming the stability of our EMR, ERP, and IAM modules. Tenant isolation has been verified at the database level using PostgreSQL Row-Level Security.",
      "For deployment, the platform is now fully containerized and deployable to Oracle Cloud Infrastructure (OCI). The integration of dynamic feature flags allows us to configure editions (Starter, Professional, Enterprise, Network, and Government) on a per-tenant basis without code alterations.",
      "With the core platform complete and verified, CyberCom is ready for production onboarding. We recommend deploying the first pilot systems using our automated tenant provisioning scripts, backed by our cross-region disaster recovery replication plan."
    ],
  },
};

export async function generateStaticParams() {
  return Object.keys(ARTICLES_CONTENT).map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: ArticlePageProps): Promise<Metadata> {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  const article = ARTICLES_CONTENT[slug];
  if (!article) return {};

  return buildMetadata({
    title: `${article.title} — Blog & News`,
    description: article.paragraphs[0] ?? "",
    path: `/blog/${slug}`,
    locale,
  });
}

export default async function ArticleDetailPage({ params }: ArticlePageProps) {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  const article = ARTICLES_CONTENT[slug];

  if (!article) notFound();

  const isAr = locale === "ar";
  const formattedDate = new Date(article.date).toLocaleDateString(isAr ? "ar-EG" : "en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="min-h-dvh pt-24 pb-16">
      <div className="section-container max-w-3xl">
        {/* Back Link */}
        <Link
          href={`/${locale}/blog`}
          className="inline-flex items-center gap-2 text-sm text-cy-gray-400 hover:text-white transition-colors mb-8 group"
        >
          <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform rtl:rotate-180" />
          {isAr ? "العودة إلى المدونة" : "Back to Blog"}
        </Link>

        {/* Article Header */}
        <article className="space-y-6">
          <div className="space-y-3">
            <span className="product-badge text-cy-orange border-cy-orange/20 bg-cy-orange/5">
              <Tag className="w-3 h-3" aria-hidden="true" />
              {article.category}
            </span>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-heading font-semibold text-white leading-tight">
              {article.title}
            </h1>
          </div>

          {/* Meta Info */}
          <div className="flex flex-wrap items-center gap-6 py-4 border-y border-cy-glass-border text-xs text-cy-gray-400">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-cy-glass-bg border border-cy-glass-border flex items-center justify-center">
                <User className="w-3.5 h-3.5 text-cy-gray-400" />
              </div>
              <div>
                <p className="font-medium text-white">{article.author}</p>
                <p className="text-2xs text-cy-gray-500">{article.authorRole}</p>
              </div>
            </div>
            <div className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5" />
              <time dateTime={article.date}>{formattedDate}</time>
            </div>
            <div className="flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5" />
              <span>{article.readTime}</span>
            </div>
          </div>

          {/* Body Paragraphs */}
          <div className="space-y-6 text-cy-gray-300 leading-relaxed text-base pt-4">
            {article.paragraphs.map((para, index) => (
              <p key={index}>{para}</p>
            ))}
          </div>
        </article>
      </div>
    </div>
  );
}
