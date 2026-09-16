"use client";

import { useEffect, useState } from "react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty } from "@/components/ui";
import { Panel, Badge } from "@/components/kit";
import { useToast } from "@/components/Toast";
import { money, fmtDate, type FamilyStatement } from "@/lib/portal";

/**
 * The consolidated family statement.
 *
 * One page for the whole household, not one per child: a parent with three
 * children was previously handed three unrelated statements and left to add
 * them up. The single number at the top is what they came for.
 */
export default function PortalFeesPage() {
  const [statement, setStatement] = useState<FamilyStatement | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [paying, setPaying] = useState<string | null>(null);
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      const families = await cyed.list<{ id: string }>("sis/families/");
      if (!families[0]) {
        setStatement(null);
        setError(null);
        return;
      }
      setStatement(
        await cyed.get<FamilyStatement>(`billing/families/${families[0].id}/statement/`),
      );
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load your statement");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const pay = async (installmentId: string, amount: string) => {
    setPaying(installmentId);
    try {
      // Creates a payment intent through the gateway seam. The school is paid
      // when the provider confirms — this button starts that, it does not
      // mark the fee paid on its own.
      const intent = await cyed.create<{ id: string; status: string; checkout_url?: string }>(
        "payments/intents/",
        { installment: installmentId, amount, method: "card" },
      );
      if (intent.checkout_url) {
        window.location.href = intent.checkout_url;
        return;
      }
      toast.push("Payment started. The school will confirm once it clears.");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not start the payment");
    } finally {
      setPaying(null);
    }
  };

  if (loading) return <SkeletonRows rows={6} />;
  if (error) return <ErrorNote error={error} />;
  if (!statement) return <Empty label="No fee account is linked to this family yet." />;

  const { totals } = statement;
  const owing = Number(totals.balance);
  const overdue = Number(totals.overdue);
  const discount = Number(totals.sibling_discount_applied);

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader title="Fees" subtitle={statement.name} />

      <Panel>
        <div style={{ display: "grid", gap: "0.35rem" }}>
          <span className="label">Total owing</span>
          <div
            style={{
              fontSize: "2.25rem",
              fontWeight: 900,
              color: overdue > 0 ? "var(--red, #f87171)" : undefined,
            }}
          >
            {money(owing)}
          </div>
          {overdue > 0 && (
            <div style={{ color: "var(--red, #f87171)", fontSize: "0.9rem" }}>
              {money(overdue)} of this is overdue.
            </div>
          )}
          {discount > 0 && (
            <div style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
              Includes {money(discount)} of sibling discount.
            </div>
          )}
          <div style={{ color: "var(--muted)", fontSize: "0.85rem", marginTop: "0.35rem" }}>
            {money(totals.paid)} paid of {money(totals.billed)} billed across{" "}
            {statement.children_total} {statement.children_total === 1 ? "child" : "children"}.
          </div>
        </div>
      </Panel>

      {statement.children.map((c) => (
        <Panel
          key={c.student}
          title={c.name}
          action={
            Number(c.balance) > 0 ? (
              <span style={{ fontWeight: 700 }}>{money(c.balance)}</span>
            ) : (
              <Badge value="settled" />
            )
          }
        >
          {c.sibling_discount?.rule && (
            <div style={{ color: "var(--muted)", fontSize: "0.85rem", marginBottom: "0.6rem" }}>
              {c.sibling_discount.rule}: {c.sibling_discount.percent}% off tuition (
              {money(c.sibling_discount.amount_off)}).
            </div>
          )}

          {c.installments.length === 0 && c.invoices.length === 0 && (
            <Empty label="Nothing billed for this child yet." />
          )}

          {c.installments.map((i) => (
            <div
              key={i.installment}
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: "0.75rem",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "0.7rem 0",
                borderBottom: "1px solid var(--border)",
              }}
            >
              <div>
                <div style={{ fontWeight: 650 }}>Instalment {i.installment_no}</div>
                <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
                  Due {fmtDate(i.due_date)} · {money(i.paid)} paid of {money(i.amount_due)}
                </div>
              </div>
              <div style={{ display: "flex", gap: "0.6rem", alignItems: "center" }}>
                <Badge value={i.status} />
                <strong>{money(i.balance)}</strong>
                {Number(i.balance) > 0 && (
                  <button
                    className="btn btn-primary"
                    disabled={paying !== null}
                    onClick={() => pay(i.installment, i.balance)}
                  >
                    {paying === i.installment ? "Starting…" : "Pay"}
                  </button>
                )}
              </div>
            </div>
          ))}

          {c.invoices.map((inv) => (
            <div
              key={inv.invoice}
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: "0.75rem",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "0.7rem 0",
                borderBottom: "1px solid var(--border)",
              }}
            >
              <div>
                <div style={{ fontWeight: 650 }}>{inv.description || "Invoice"}</div>
                <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
                  Due {fmtDate(inv.due_date)}
                </div>
              </div>
              <div style={{ display: "flex", gap: "0.6rem", alignItems: "center" }}>
                <Badge value={inv.status} />
                <strong>{money(inv.balance)}</strong>
              </div>
            </div>
          ))}
        </Panel>
      ))}

      <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
        Questions about your account? Message the school from the Messages tab, or contact the
        office. Payments can take a day or two to appear here after they clear.
      </p>
    </div>
  );
}
