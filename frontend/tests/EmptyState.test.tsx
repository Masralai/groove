import { render, screen, fireEvent } from "@testing-library/react";
import EmptyState from "@/components/EmptyState";

describe("EmptyState", () => {
  it("renders title and description", () => {
    render(<EmptyState title="No data" description="Nothing to show." />);
    expect(screen.getByText("No data")).toBeInTheDocument();
    expect(screen.getByText("Nothing to show.")).toBeInTheDocument();
  });

  it("renders action button and fires onClick", () => {
    const onClick = vi.fn();
    render(
      <EmptyState
        title="No campaigns"
        description="Sync your data."
        action={{ label: "Sync Now", onClick }}
      />
    );
    const btn = screen.getByText("Sync Now");
    expect(btn).toBeInTheDocument();
    fireEvent.click(btn);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("renders chat variant with chat icon", () => {
    render(
      <EmptyState
        variant="chat"
        title="Ask about your data"
        description="Type a question."
      />
    );
    expect(screen.getByText("Ask about your data")).toBeInTheDocument();
    expect(screen.getByText("Type a question.")).toBeInTheDocument();
  });

  it("renders custom icon when provided", () => {
    render(
      <EmptyState
        title="Hello"
        description="World"
        icon={<span data-testid="custom-icon">*</span>}
      />
    );
    expect(screen.getByTestId("custom-icon")).toBeInTheDocument();
  });
});
