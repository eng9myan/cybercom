import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { EmptyCard, ErrorCard, LoadingCard } from '../CycomEmptyStates';

describe('CycomEmptyStates', () => {
  it('LoadingCard renders default label', () => {
    render(<LoadingCard />);
    expect(screen.getByText('Loading from Cycom backend…')).toBeInTheDocument();
  });

  it('ErrorCard renders the error and default hint', () => {
    render(<ErrorCard error="Network timeout" />);
    expect(screen.getByText('Network timeout')).toBeInTheDocument();
    expect(screen.getByText(/Confirm the Cycom backend is running/)).toBeInTheDocument();
  });

  it('EmptyCard renders a custom label', () => {
    render(<EmptyCard label="No vendors yet." />);
    expect(screen.getByText('No vendors yet.')).toBeInTheDocument();
  });
});
