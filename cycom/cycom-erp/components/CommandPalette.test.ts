import { describe, expect, it } from 'vitest';
import { score } from './CommandPalette';

/**
 * The palette's whole value is that a 2-4 letter query lands on the screen
 * you meant. These lock the ranking rules that make that true.
 */

function rank(query: string, candidates: string[]): string[] {
  return candidates
    .map((c) => ({ c, s: score(query, c) }))
    .filter((r): r is { c: string; s: number } => r.s !== null)
    .sort((a, b) => b.s - a.s)
    .map((r) => r.c);
}

describe('command palette matching', () => {
  it('matches a subsequence, not just a substring', () => {
    expect(score('por', 'Purchase Orders')).not.toBeNull();
    expect(score('gnt', 'Gantt & Critical Path')).not.toBeNull();
  });

  it('rejects text that lacks the letters in order', () => {
    expect(score('zzz', 'Purchase Orders')).toBeNull();
    expect(score('redro', 'Orders')).toBeNull(); // right letters, wrong order
  });

  it('ranks a prefix hit above a mid-string hit', () => {
    const [first] = rank('inv', ['Customer Invoices', 'Inventory']);
    expect(first).toBe('Inventory');
  });

  it('ranks a word-start hit above an arbitrary substring', () => {
    const [first] = rank('map', ['Company Map Data', 'Warehouse Map']);
    expect(first).toBe('Warehouse Map');
  });

  it('ranks an exact-ish short name above a longer one containing it', () => {
    const [first] = rank('payroll', ['Payroll', 'Payroll Deductions and Lateness']);
    expect(first).toBe('Payroll');
  });

  it('is case insensitive and ignores surrounding whitespace', () => {
    expect(score('  INVENTORY ', 'Inventory')).toEqual(score('inventory', 'Inventory'));
  });

  it('treats an empty query as a neutral match so the full list shows', () => {
    expect(score('', 'Anything')).toBe(0);
  });

  it('puts the obvious screen first for a realistic short query', () => {
    const screens = [
      'Sales', 'Point of Sale', 'Purchase', 'Inventory', 'Warehouse Map',
      'Accounting', 'Bank Reconciliation', 'Payroll', 'Automation', 'Settings',
    ];
    expect(rank('rec', screens)[0]).toBe('Bank Reconciliation');
    expect(rank('auto', screens)[0]).toBe('Automation');
    expect(rank('pos', screens)[0]).toBe('Point of Sale');
  });
});
