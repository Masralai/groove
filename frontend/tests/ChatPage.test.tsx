import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ChatPage from "@/app/chat/page";

beforeEach(() => {
  vi.spyOn(global, "fetch").mockImplementation(
    (url: string | URL | Request, init?: RequestInit) => {
      const urlStr = url.toString();
      if (urlStr.includes("/api/chat") && init?.method === "POST") {
        const body = JSON.parse(init.body as string);
        if (body.query === "fail") {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                error: "sql_generation_failed",
                message: "I couldn't generate a valid query.",
              }),
              { status: 400 }
            )
          );
        }
        return Promise.resolve(
          new Response(
            JSON.stringify({
              answer: "The campaign spent $500 last week.",
              sql: "SELECT SUM(spend) FROM insights WHERE date >= CURRENT_DATE - INTERVAL '1 week'",
              data: [{ sum: 500 }],
            }),
            { status: 200 }
          )
        );
      }
      return Promise.resolve(new Response("{}", { status: 200 }));
    }
  );
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ChatPage", () => {
  it("renders empty state initially", () => {
    render(<ChatPage />);
    expect(screen.getByText("Ask about your ad data")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("Ask about your Meta Ads data...")
    ).toBeInTheDocument();
  });

  it("sends a message and displays response", async () => {
    render(<ChatPage />);
    const input = screen.getByPlaceholderText("Ask about your Meta Ads data...");
    const sendBtn = screen.getByText("Send");

    fireEvent.change(input, { target: { value: "How much did we spend?" } });
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(
        screen.getByText("How much did we spend?")
      ).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(
        screen.getByText("The campaign spent $500 last week.")
      ).toBeInTheDocument();
    });
  });

  it("shows error message on API failure", async () => {
    render(<ChatPage />);
    const input = screen.getByPlaceholderText("Ask about your Meta Ads data...");
    const sendBtn = screen.getByText("Send");

    fireEvent.change(input, { target: { value: "fail" } });
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(
        screen.getByText("I couldn't generate a valid query.")
      ).toBeInTheDocument();
    });
  });

  it("disables send button when input is empty", () => {
    render(<ChatPage />);
    const sendBtn = screen.getByText("Send");
    expect(sendBtn.closest("button")).toBeDisabled();
  });

  it("shows user-friendly error on non-JSON response", async () => {
    render(<ChatPage />);
    const input = screen.getByPlaceholderText("Ask about your Meta Ads data...");
    const sendBtn = screen.getByText("Send");

    fireEvent.change(input, { target: { value: "test" } });

    vi.mocked(global.fetch).mockImplementationOnce(() =>
      Promise.resolve(
        new Response("<html>502 Bad Gateway</html>", {
          status: 502,
          statusText: "Bad Gateway",
          headers: { "Content-Type": "text/html" },
        })
      )
    );

    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(screen.getByText("Server error (502)")).toBeInTheDocument();
    });
  });

});
