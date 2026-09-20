import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { EmptyCard, ErrorCard, LoadingCard } from '../ProviderPortalEmptyStates';

describe('ProviderPortalEmptyStates', () => {
  it('LoadingCard renders default label', () => {
    render(<LoadingCard />);
    expect(screen.getByText('Loading from CyMed backend…')).toBeInTheDocument();
  });

  it('ErrorCard renders the error and default hint', () => {
    render(<ErrorCard error="Network timeout" />);
    expect(screen.getByText('Network timeout')).toBeInTheDocument();
    expect(screen.getByText(/Confirm the CyMed backend is running/)).toBeInTheDocument();
  });

  it('EmptyCard renders a custom label', () => {
    render(<EmptyCard label="No providers yet." />);
    expect(screen.getByText('No providers yet.')).toBeInTheDocument();
  });
});
