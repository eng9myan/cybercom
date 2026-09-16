"use client";

import { useEffect, useState } from "react";
import { Download } from "lucide-react";
import { cyed, cyedUrl } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty } from "@/components/ui";
import { Panel, Badge } from "@/components/kit";
import { Note } from "@/app/portal/_parts";
import { fmtDate } from "@/lib/portal";
import type { ReportCard } from "@/lib/types";

/**
 * A student's own published reports.
 *
 * Students could see individual marks but not the report those marks became,
 * which is the document they are actually asked about at home. Drafts stay
 * hidden — a report mid-edit shows grades that are about to change.
 */
export default function StudentReportsPage() {
  const [cards, setCards] = useState<ReportCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setCards(await cyed.list<ReportCard>("reporting/report-cards/?status=published"));
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not load your reports");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <SkeletonRows rows={4} />;
  if (error) return <ErrorNote error={error} />;

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader title="My reports" subtitle="Published report cards" />

      {cards.length === 0 && <Empty label="No reports have been published yet." />}

      {cards.map((card) => (
        <Panel key={card.id} title={card.term} action={<Badge value={card.status} />}>
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: "0.75rem",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
              Published {fmtDate(card.published_on)}
            </div>
            <a
              className="btn btn-primary"
              href={cyedUrl(`reporting/report-cards/${card.id}/pdf/`)}
              target="_blank"
              rel="noreferrer"
            >
              <Download size={15} style={{ marginRight: 6 }} />
              Download PDF
            </a>
          </div>
          {card.general_comment && (
            <p style={{ marginTop: "0.9rem", lineHeight: 1.55 }}>{card.general_comment}</p>
          )}
        </Panel>
      ))}

      <Note>Your family can also see these reports in their portal.</Note>
    </div>
  );
}
