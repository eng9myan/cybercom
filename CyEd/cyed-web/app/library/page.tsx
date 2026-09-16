"use client";

import { useCallback, useEffect, useState } from "react";
import { BookOpen, RotateCcw, AlertTriangle } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty, Field } from "@/components/ui";
import { Panel, Badge, Segmented } from "@/components/kit";
import { useToast } from "@/components/Toast";
import { fmtDate, money } from "@/lib/portal";

/**
 * Library circulation.
 *
 * Opens on what is out and overdue rather than the catalogue, because a
 * librarian at the desk is either issuing a book, taking one back, or chasing
 * one — browsing the shelf list is not a daily task.
 *
 * Fines are shown as they accrue but can only be changed through the waiver
 * action, with a reason. A fine that can be typed over is not a fine, and
 * "why was this waived" is the question an audit asks.
 */

type Loan = {
  id: string;
  book: string;
  book_title: string;
  student: string;
  student_name: string;
  borrowed_on: string;
  due_on: string;
  returned_on: string | null;
  status: string;
  fine_amount: string;
  fine_waived: boolean;
  fine_waive_reason: string;
  days_overdue: number;
  outstanding_fine: string;
  renewed_count: number;
};

type Book = {
  id: string;
  title: string;
  author: string;
  category: string;
  copies_total: number;
  copies_available: number;
};

type Student = { id: string; first_name: string; last_name: string; year_level: number };

export default function LibraryPage() {
  const [view, setView] = useState<"onloan" | "overdue" | "catalogue">("onloan");
  const [loans, setLoans] = useState<Loan[]>([]);
  const [books, setBooks] = useState<Book[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [waiving, setWaiving] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const [issueBook, setIssueBook] = useState("");
  const [issueStudent, setIssueStudent] = useState("");
  const toast = useToast();

  const load = useCallback(async () => {
    try {
      const [loanRows, bookRows] = await Promise.all([
        cyed.list<Loan>("library/loans/"),
        cyed.list<Book>("library/books/"),
      ]);
      setLoans(loanRows);
      setBooks(bookRows);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load the library");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    (async () => {
      try {
        setStudents(await cyed.list<Student>("sis/students/"));
      } catch {
        // Issuing degrades; the desk views still work.
      }
    })();
  }, [load]);

  const act = async (loan: Loan, path: string, body?: unknown, done?: string) => {
    setBusy(loan.id);
    try {
      await cyed.action(`library/loans/${loan.id}/${path}/`, body);
      toast.push(done ?? "Done.");
      setWaiving(null);
      setReason("");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "That did not work");
    } finally {
      setBusy(null);
    }
  };

  const issue = async () => {
    if (!issueBook || !issueStudent) return;
    setBusy("issue");
    try {
      // The due date comes from library policy server-side, never from here.
      await cyed.create("library/loans/", { book: issueBook, student: issueStudent });
      toast.push("Issued.");
      setIssueBook("");
      setIssueStudent("");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not issue that book");
    } finally {
      setBusy(null);
    }
  };

  const sweep = async () => {
    setBusy("sweep");
    try {
      const r = await cyed.action<{ updated: number }>("library/loans/mark-overdue/");
      toast.push(`${r.updated} loan(s) flipped to overdue.`);
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not run the sweep");
    } finally {
      setBusy(null);
    }
  };

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;

  const out = loans.filter((l) => !l.returned_on);
  const overdue = out.filter((l) => l.days_overdue > 0);
  const owed = overdue.reduce((sum, l) => sum + Number(l.outstanding_fine || 0), 0);
  const rows = view === "overdue" ? overdue : out;

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader
        title="Library"
        subtitle="Issue, return and chase"
        action={
          <Segmented
            value={view}
            onChange={setView}
            options={[
              { value: "onloan", label: `On loan (${out.length})` },
              { value: "overdue", label: `Overdue (${overdue.length})` },
              { value: "catalogue", label: "Catalogue" },
            ]}
          />
        }
      />

      <div
        style={{
          display: "grid",
          gap: "0.6rem",
          gridTemplateColumns: "repeat(auto-fit, minmax(10rem, 1fr))",
        }}
      >
        <Count label="On loan" value={String(out.length)} />
        <Count label="Overdue" value={String(overdue.length)} tone={overdue.length ? "bad" : "ok"} />
        <Count label="Fines outstanding" value={money(owed)} tone={owed > 0 ? "warn" : "ok"} />
        <Count label="Titles" value={String(books.length)} />
      </div>

      {view !== "catalogue" && (
        <>
          <Panel title="Issue a book">
            <div
              style={{
                display: "grid",
                gap: "0.9rem",
                gridTemplateColumns: "repeat(auto-fit, minmax(13rem, 1fr))",
                alignItems: "end",
              }}
            >
              <Field label="Book">
                <select className="input" value={issueBook} onChange={(e) => setIssueBook(e.target.value)}>
                  <option value="">Choose…</option>
                  {books.map((b) => (
                    <option key={b.id} value={b.id} disabled={b.copies_available < 1}>
                      {b.title}
                      {b.copies_available < 1 ? " — none available" : ` — ${b.copies_available} free`}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Borrower">
                <select
                  className="input"
                  value={issueStudent}
                  onChange={(e) => setIssueStudent(e.target.value)}
                >
                  <option value="">Choose…</option>
                  {students.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.first_name} {s.last_name} — Year {s.year_level}
                    </option>
                  ))}
                </select>
              </Field>
              <button
                className="btn btn-primary"
                disabled={!issueBook || !issueStudent || busy !== null}
                onClick={issue}
              >
                <BookOpen size={15} style={{ marginRight: 6 }} />
                Issue
              </button>
            </div>
          </Panel>

          {rows.length === 0 ? (
            <Empty label={view === "overdue" ? "Nothing is overdue." : "Nothing is on loan."} />
          ) : (
            <Panel
              pad={false}
              action={
                view === "overdue" && (
                  <button className="btn" style={{ margin: "0 1rem" }} disabled={busy !== null} onClick={sweep}>
                    Run overdue sweep
                  </button>
                )
              }
            >
              {rows.map((loan) => (
                <div
                  key={loan.id}
                  style={{
                    padding: "0.85rem 1.1rem",
                    borderBottom: "1px solid var(--border)",
                    background:
                      loan.days_overdue > 0
                        ? "color-mix(in srgb, var(--red, #f87171) 7%, transparent)"
                        : undefined,
                  }}
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
                    <div>
                      <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                        {loan.days_overdue > 0 && (
                          <AlertTriangle size={15} style={{ color: "var(--red, #f87171)" }} />
                        )}
                        <strong>{loan.book_title}</strong>
                        <Badge value={loan.status} />
                        {loan.fine_waived && <Badge value="fine waived" />}
                      </div>
                      <div style={{ fontSize: "0.83rem", color: "var(--muted)", marginTop: 2 }}>
                        {loan.student_name} · due {fmtDate(loan.due_on)}
                        {loan.days_overdue > 0 && ` · ${loan.days_overdue} days overdue`}
                        {Number(loan.outstanding_fine) > 0 &&
                          ` · ${money(loan.outstanding_fine)} owing`}
                        {loan.renewed_count > 0 && ` · renewed ${loan.renewed_count}×`}
                      </div>
                      {loan.fine_waived && loan.fine_waive_reason && (
                        <div style={{ fontSize: "0.8rem", color: "var(--faint)", marginTop: 2 }}>
                          Waived: {loan.fine_waive_reason}
                        </div>
                      )}
                    </div>

                    <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
                      {Number(loan.outstanding_fine) > 0 && !loan.fine_waived && (
                        <button
                          className="btn"
                          disabled={busy !== null}
                          onClick={() => {
                            setWaiving(waiving === loan.id ? null : loan.id);
                            setReason("");
                          }}
                        >
                          Waive fine
                        </button>
                      )}
                      <button
                        className="btn"
                        disabled={busy !== null || loan.days_overdue > 0}
                        title={
                          loan.days_overdue > 0
                            ? "An overdue loan cannot be renewed — take it back first"
                            : undefined
                        }
                        onClick={() => act(loan, "renew", undefined, "Renewed.")}
                      >
                        <RotateCcw size={14} style={{ marginRight: 4 }} />
                        Renew
                      </button>
                      <button
                        className="btn btn-primary"
                        disabled={busy !== null}
                        onClick={() => act(loan, "return_book", undefined, "Returned.")}
                      >
                        Return
                      </button>
                    </div>
                  </div>

                  {waiving === loan.id && (
                    <div style={{ marginTop: "0.7rem", display: "grid", gap: "0.5rem" }}>
                      <input
                        className="input"
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                        placeholder="Why is this fine being waived? This is recorded."
                      />
                      <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end" }}>
                        <button className="btn" onClick={() => setWaiving(null)}>
                          Cancel
                        </button>
                        <button
                          className="btn btn-primary"
                          disabled={!reason.trim() || busy !== null}
                          onClick={() => act(loan, "waive-fine", { reason }, "Fine waived.")}
                        >
                          Waive
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </Panel>
          )}
        </>
      )}

      {view === "catalogue" &&
        (books.length === 0 ? (
          <Empty label="No titles yet." />
        ) : (
          <Panel pad={false}>
            {books.map((b) => (
              <div
                key={b.id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: "0.75rem",
                  padding: "0.75rem 1.1rem",
                  borderBottom: "1px solid var(--border)",
                }}
              >
                <div>
                  <strong>{b.title}</strong>
                  <div style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
                    {b.author}
                    {b.category && ` · ${b.category}`}
                  </div>
                </div>
                <span
                  style={{
                    fontSize: "0.85rem",
                    color: b.copies_available ? "var(--muted)" : "var(--amber, #fbbf24)",
                    whiteSpace: "nowrap",
                  }}
                >
                  {b.copies_available} of {b.copies_total} on shelf
                </span>
              </div>
            ))}
          </Panel>
        ))}
    </div>
  );
}

function Count({ label, value, tone }: { label: string; value: string; tone?: "ok" | "bad" | "warn" }) {
  const colour =
    tone === "bad" ? "var(--red, #f87171)"
      : tone === "warn" ? "var(--amber, #fbbf24)"
        : tone === "ok" ? "var(--green, #34d399)" : undefined;
  return (
    <div className="card p-5" style={{ display: "grid", gap: "0.2rem" }}>
      <span className="label">{label}</span>
      <strong style={{ fontSize: "1.7rem", color: colour }}>{value}</strong>
    </div>
  );
}
