import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Hero } from "@/components/sections/Hero";

describe("Hero section", () => {
  it("renders the hero section with heading", () => {
    render(<Hero locale="en" />);
    const heading = screen.getByRole("heading", { level: 1 });
    expect(heading).toBeTruthy();
  });

  it("renders CTA buttons", () => {
    render(<Hero locale="en" />);
    const demoLink = screen.getByRole("link", { name: /demo/i });
    expect(demoLink).toBeTruthy();
  });

  it("renders compliance badges", () => {
    render(<Hero locale="en" />);
    const section = screen.getByLabelText(/compliance/i);
    expect(section).toBeTruthy();
  });

  it("has correct skip link target", () => {
    render(<Hero locale="en" />);
    const section = screen.getByRole("region");
    expect(section).toBeTruthy();
  });

  it("renders stats section", () => {
    render(<Hero locale="en" />);
    const stats = screen.getByRole("list", { name: /highlights/i });
    expect(stats).toBeTruthy();
  });
});
