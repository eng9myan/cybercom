import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DemoSection } from "@/components/sections/DemoSection";
import { demoApi } from "@cybercom/api";

describe("DemoSection form", () => {
  it("renders all form fields", () => {
    render(<DemoSection locale="en" />);
    expect(screen.getByLabelText(/full name/i)).toBeTruthy();
    expect(screen.getByLabelText(/work email/i)).toBeTruthy();
    expect(screen.getByLabelText(/job title/i)).toBeTruthy();
    expect(screen.getByLabelText(/company name/i)).toBeTruthy();
    expect(screen.getByLabelText(/country/i)).toBeTruthy();
  });

  it("shows validation errors when submitted empty", async () => {
    const user = userEvent.setup();
    render(<DemoSection locale="en" />);
    const submitBtn = screen.getByRole("button", { name: /submit|request demo/i });
    await user.click(submitBtn);
    await waitFor(() => {
      expect(screen.getByText(/full name is required/i)).toBeTruthy();
    });
  });

  it("shows product selection", () => {
    render(<DemoSection locale="en" />);
    expect(screen.getByText("CyMed Hospital")).toBeTruthy();
    expect(screen.getByText("CyIdentity")).toBeTruthy();
  });

  it("requires GDPR consent", async () => {
    const user = userEvent.setup();
    render(<DemoSection locale="en" />);
    const submitBtn = screen.getByRole("button", { name: /submit|request demo/i });
    await user.click(submitBtn);
    await waitFor(() => {
      expect(screen.getByText(/must agree/i)).toBeTruthy();
    });
  });

  it("shows success state after successful submission", async () => {
    vi.mocked(demoApi.submit).mockResolvedValue({
      id: "1",
      reference_number: "CYB-999888",
      status: "pending",
      created_at: new Date().toISOString(),
    });

    const user = userEvent.setup();
    render(<DemoSection locale="en" />);

    await user.type(screen.getByLabelText(/full name/i), "Sara Al-Nour");
    await user.type(screen.getByLabelText(/work email/i), "sara@hospital.sa");
    await user.type(screen.getByLabelText(/job title/i), "CIO");
    await user.type(screen.getByLabelText(/company name/i), "Test Hospital");
    await user.type(screen.getByLabelText(/country/i), "Saudi Arabia");
    await user.click(screen.getByRole("button", { name: /cymed hospital/i }));
    await user.click(screen.getByRole("checkbox", { name: /privacy/i }));
    await user.click(screen.getByRole("button", { name: /submit|request demo/i }));

    await waitFor(() => {
      expect(screen.getByText(/CYB-999888/)).toBeTruthy();
    });
  });
});
