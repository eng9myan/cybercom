import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import CyaiChatWidget from '../CyaiChatWidget';

describe('CyaiChatWidget', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ answer: 'No overdue invoices.', plan_used: 'overdue_invoices' }),
      }),
    );
  });

  it('is closed by default and opens on click', () => {
    render(<CyaiChatWidget />);
    expect(screen.queryByText('CyAI Assistant')).not.toBeInTheDocument();
    fireEvent.click(screen.getByLabelText('Open CyAI assistant'));
    expect(screen.getByText('CyAI Assistant')).toBeInTheDocument();
  });

  it('shows starter questions and asking one sends a real request and renders the answer', async () => {
    render(<CyaiChatWidget />);
    fireEvent.click(screen.getByLabelText('Open CyAI assistant'));

    const starter = screen.getByText('How many overdue invoices exist?');
    fireEvent.click(starter);

    expect(fetch).toHaveBeenCalledWith(
      '/api/cycom/cyai/ask',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ question: 'How many overdue invoices exist?' }),
      }),
    );

    await waitFor(() => {
      expect(screen.getByText('No overdue invoices.')).toBeInTheDocument();
    });
  });

  it('renders a typed question and submits via the form', async () => {
    render(<CyaiChatWidget />);
    fireEvent.click(screen.getByLabelText('Open CyAI assistant'));

    const input = screen.getByPlaceholderText(/Ask about sales/);
    fireEvent.change(input, { target: { value: 'What is the current stock of Widget?' } });
    fireEvent.submit(input.closest('form')!);

    await waitFor(() => {
      expect(screen.getByText('What is the current stock of Widget?')).toBeInTheDocument();
    });
  });
});
