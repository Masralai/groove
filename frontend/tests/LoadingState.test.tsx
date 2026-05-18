import { render, screen } from "@testing-library/react";
import LoadingState from "@/components/LoadingState";

describe("LoadingState", () => {
  it("renders card skeletons by default", () => {
    const { container } = render(<LoadingState />);
    expect(screen.getByRole("status")).toBeInTheDocument();
    const skeletons = container.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("renders specified number of card skeletons", () => {
    const { container } = render(<LoadingState rows={2} />);
    const cards = container.querySelectorAll(".animate-pulse");
    expect(cards.length).toBe(2);
  });

  it("renders table skeletons", () => {
    render(<LoadingState type="table" rows={3} />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });
});
