import { render, screen } from "@testing-library/react";
import Header from "@/app/_components/Header";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

describe("Header", () => {
  it("renders logo with Groove text", () => {
    render(<Header />);
    expect(screen.getByText("Groove")).toBeInTheDocument();
  });

  it("renders navigation links", () => {
    render(<Header />);
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Chat")).toBeInTheDocument();
  });

  it("renders query button", () => {
    render(<Header />);
    const buttons = screen.getAllByText("Query Your Data");
    expect(buttons.length).toBeGreaterThanOrEqual(1);
  });

  it("has menu toggle button for mobile", () => {
    render(<Header />);
    const menuBtn = screen.getByLabelText("Open menu");
    expect(menuBtn).toBeInTheDocument();
  });
});
