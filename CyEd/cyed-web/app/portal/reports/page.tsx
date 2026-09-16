"use client";

import { useEffect, useState } from "react";
import { Download } from "lucide-react";
import { cyed, cyedUrl } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty } from "@/components/ui";
import { Panel, Badge } from "@/components/kit";
import { Note, PersonSwitcher } from "@/app/portal/_parts";
import { fmtDate, useMyChildren } from "@/lib/portal";
import type { ReportCard } from "@/lib/types";

/**
 * Published report cards, with the PDF download.
 *
 * Only published reports appear — a draft is a teacher's working document, and
 * a parent seeing one mid-edit would read grades that are about to change.
 */
export default function PortalReportsPage() {
  const { children, selected, setSelected, loading, error } = useMyChildren();
  const [cards, setCards] = useState<ReportCard[]>([]);
  const [loadingCards, setLoadingCards] = useState(false);
  const [cardError, setCardError] = useState<string | null>(null);

  useEffect(() => {
    if (!selected) return;
    setLoadingCards(true);
    (async () => {
      try {
        const rows = await cyed.list<ReportCard>(
          `reporting/report-cards/?student=${selected}&status=published`,
        );
        setCards(rows);
        setCardError(null);
      } catch (e) {
        setCardError(e instanceof Error ? e.message : "Could not load reports");
      } finally {
        setLoadingCards(false);
      }
    })();
  }, [selected]);

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;
  if (!children.length) return <Empty label="No children are linked to this account yet." />;

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader title="Reports" subtitle="Published report cards" />
      <PersonSwitcher people={children} value={selected} onChange={setSelected} label="Viewing" />

      {cardError && <ErrorNote error={cardError} />}
      {loadingCards && <SkeletonRows rows={3} />}

      {!loadingCards && cards.length === 0 && (
        <Empty label="No reports have been published for this child yet." />
      )}

      {cards.map((card) => (
        <Panel
          key={card.id}
          title={card.term}
          action={<Badge value={card.status} />}
        >
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

      <Note>
        Each report carries a content hash, so the school can confirm a downloaded copy has not been
        altered.
      </Note>
    </div>
  );
}
