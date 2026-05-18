import { render, screen } from "@testing-library/react";
import KPICard from "@/components/KPICard";

describe("KPICard", () => {
  const defaultProps = {
    title: "Total Spend",
    value: "$12.5K",
    change: "+15.3%",
    trend: "up" as const,
    icon: <svg data-testid="test-icon" />,
  };

  it("renders title and value", () => {
    render(<KPICard {...defaultProps} />);
    expect(screen.getByText("Total Spend")).toBeInTheDocument();
    expect(screen.getByText("$12.5K")).toBeInTheDocument();
  });

  it("renders trend indicator for up trend", () => {
    render(<KPICard {...defaultProps} />);
    expect(screen.getByText("+15.3%")).toBeInTheDocument();
    expect(screen.getByText("vs last month")).toBeInTheDocument();
  });

  it("shows down trend styling for negative trend", () => {
    render(<KPICard {...defaultProps} trend="down" change="-5.2%" />);
    expect(screen.getByText("-5.2%")).toBeInTheDocument();
  });

  it("renders the icon", () => {
    render(<KPICard {...defaultProps} />);
    expect(screen.getByTestId("test-icon")).toBeInTheDocument();
  });
});
