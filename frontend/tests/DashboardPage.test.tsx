import { render, screen, waitFor } from "@testing-library/react";
import DashboardPage from "@/app/dashboard/page";

const mockCampaigns = [
  {
    id: "1",
    name: "Test Campaign",
    status: "ACTIVE",
    objective: "LINK_CLICKS",
    daily_budget: 5000,
    lifetime_budget: null,
    created_time: "2025-01-01T00:00:00+00:00",
  },
  {
    id: "2",
    name: "Paused Campaign",
    status: "PAUSED",
    objective: "CONVERSIONS",
    daily_budget: null,
    lifetime_budget: 100000,
    created_time: "2025-02-01T00:00:00+00:00",
  },
];

const mockInsights = [
  { spend: 100, impressions: 1000, clicks: 50 },
  { spend: 200, impressions: 2000, clicks: 100 },
];

beforeEach(() => {
  vi.spyOn(global, "fetch").mockImplementation(
    (url: string | URL | Request) => {
      const urlStr = url.toString();
      if (urlStr.includes("/api/campaigns")) {
        return Promise.resolve(
          new Response(JSON.stringify(mockCampaigns), { status: 200 })
        );
      }
      if (urlStr.includes("/api/insights")) {
        return Promise.resolve(
          new Response(JSON.stringify(mockInsights), { status: 200 })
        );
      }
      return Promise.resolve(new Response("{}", { status: 200 }));
    }
  );
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("DashboardPage", () => {
  it("renders the dashboard heading", async () => {
    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("Dashboard")).toBeInTheDocument();
    });
  });

  it("shows KPI cards after loading", async () => {
    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("$300.00")).toBeInTheDocument();
      expect(screen.getByText("3.0K")).toBeInTheDocument();
      expect(screen.getByText("150")).toBeInTheDocument();
      expect(screen.getByText("5.00%")).toBeInTheDocument();
    });
  });

  it("renders campaigns table with campaign names", async () => {
    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("Test Campaign")).toBeInTheDocument();
      expect(screen.getByText("Paused Campaign")).toBeInTheDocument();
    });
  });

  it("renders status filter dropdown", async () => {
    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByLabelText("Filter campaigns by status")).toBeInTheDocument();
    });
  });

  it("renders sync data button", async () => {
    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("Sync Data")).toBeInTheDocument();
    });
  });
});
